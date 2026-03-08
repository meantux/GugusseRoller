#include "GCamera.h"

#include <libcamera/control_ids.h>
#include <libcamera/property_ids.h>

#include <sys/mman.h>

#include <chrono>
#include <cmath>
#include <cstring>
#include <iostream>
#include <stdexcept>

using namespace libcamera;

// ─────────────────────────────────────────────────────────────────────────────
// Construction / destruction
// ─────────────────────────────────────────────────────────────────────────────
GCamera::GCamera(const Config &cfg) : cfg_(cfg) {}

GCamera::~GCamera() {
    stop();
}

// ─────────────────────────────────────────────────────────────────────────────
// start()
// ─────────────────────────────────────────────────────────────────────────────
bool GCamera::start() {
    manager_ = std::make_unique<CameraManager>();
    if (manager_->start() < 0) {
        std::cerr << "GCamera: failed to start CameraManager\n";
        return false;
    }

    auto cameras = manager_->cameras();
    if (cameras.empty()) {
        std::cerr << "GCamera: no cameras found\n";
        return false;
    }
    // Use the first camera (there is only one on the Gugusse Roller).
    std::string camId = cameras[0]->id();
    camera_ = manager_->get(camId);
    if (!camera_) {
        std::cerr << "GCamera: could not get camera " << camId << "\n";
        return false;
    }
    if (camera_->acquire() < 0) {
        std::cerr << "GCamera: failed to acquire camera\n";
        return false;
    }

    // ── Configure raw stream at full sensor resolution ────────────────────
    camConfig_ = camera_->generateConfiguration({StreamRole::Raw});
    if (!camConfig_) {
        std::cerr << "GCamera: failed to generate configuration\n";
        return false;
    }

    StreamConfiguration &rawCfg = camConfig_->at(0);

    // Request full sensor resolution — libcamera will pick the closest
    // supported sensor mode.
    auto sensorSizes = camera_->properties()
                           .get(properties::PixelArrayActiveAreas);
    if (sensorSizes && !sensorSizes->empty()) {
        rawCfg.size = (*sensorSizes)[0].size();
    }

    // Horizontal / vertical flip
    Transform t = Transform::Identity;
    if (cfg_.hflip) t = t | Transform::HFlip;
    if (cfg_.vflip) t = t | Transform::VFlip;
    camConfig_->transform = t;

    CameraConfiguration::Status status = camConfig_->validate();
    if (status == CameraConfiguration::Invalid) {
        std::cerr << "GCamera: camera configuration is invalid\n";
        return false;
    }
    if (status == CameraConfiguration::Adjusted) {
        std::cout << "GCamera: configuration was adjusted by libcamera\n";
    }

    if (camera_->configure(camConfig_.get()) < 0) {
        std::cerr << "GCamera: camera configure() failed\n";
        return false;
    }

    // ── Read back actual stream parameters ────────────────────────────────
    StreamConfiguration &applied = camConfig_->at(0);
    width_  = applied.size.width;
    height_ = applied.size.height;
    stride_ = applied.stride;
    rawStream_ = applied.stream();

    std::cout << "GCamera: " << width_ << "x" << height_
              << " stride=" << stride_
              << " format=" << applied.pixelFormat.toString() << "\n";

    // ── Read CFA pattern from camera properties ───────────────────────────
    auto cfaOpt = camera_->properties()
                      .get(properties::draft::ColorFilterArrangement);
    if (cfaOpt) {
        cfaPattern_ = static_cast<CfaPattern>(*cfaOpt);
        std::cout << "GCamera: CFA pattern = " << static_cast<int>(*cfaOpt) << "\n";
    } else {
        std::cout << "GCamera: CFA pattern not reported, defaulting to BGGR\n";
        cfaPattern_ = CfaPattern::BGGR;
    }

    // ── Allocate frame buffers ────────────────────────────────────────────
    allocator_ = std::make_unique<FrameBufferAllocator>(camera_);
    if (allocator_->allocate(rawStream_) < 0) {
        std::cerr << "GCamera: buffer allocation failed\n";
        return false;
    }

    // ── Create a small pool of requests (double-buffering) ────────────────
    const auto &buffers = allocator_->buffers(rawStream_);
    // Use at most 4 buffers (or however many were allocated).
    int poolSize = std::min(static_cast<int>(buffers.size()), 4);
    for (int i = 0; i < poolSize; ++i) {
        auto req = camera_->createRequest(static_cast<uint64_t>(i));
        if (!req) {
            std::cerr << "GCamera: failed to create request " << i << "\n";
            return false;
        }
        if (req->addBuffer(rawStream_, buffers[i].get()) < 0) {
            std::cerr << "GCamera: addBuffer failed for request " << i << "\n";
            return false;
        }
        requests_.push_back(std::move(req));
    }

    // ── Connect completed signal ──────────────────────────────────────────
    camera_->requestCompleted.connect(this, &GCamera::onRequestCompleted);

    // ── Start camera with initial controls ───────────────────────────────
    ControlList startControls(camera_->controls());
    int64_t frameDuration = 1000000LL / cfg_.fps;
    startControls.set(controls::FrameDurationLimits,
                      Span<const int64_t, 2>({frameDuration, frameDuration}));
    startControls.set(controls::draft::NoiseReductionMode,
                      static_cast<int32_t>(controls::draft::NoiseReductionModeOff));

    if (camera_->start(&startControls) < 0) {
        std::cerr << "GCamera: camera start() failed\n";
        return false;
    }

    // Queue all requests to keep the pipeline primed
    for (auto &req : requests_) {
        camera_->queueRequest(req.get());
    }

    running_ = true;
    std::cout << "GCamera: started\n";
    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// stop()
// ─────────────────────────────────────────────────────────────────────────────
void GCamera::stop() {
    if (!running_) return;
    running_ = false;
    camera_->stop();
    allocator_->free(rawStream_);
    requests_.clear();
    camera_->requestCompleted.disconnect(this, &GCamera::onRequestCompleted);
    camera_->release();
    camera_.reset();
    manager_->stop();
    std::cout << "GCamera: stopped\n";
}

// ─────────────────────────────────────────────────────────────────────────────
// Camera controls
// ─────────────────────────────────────────────────────────────────────────────
void GCamera::setAeEnabled(bool enabled) {
    ControlList ctrls(camera_->controls());
    ctrls.set(controls::AeEnable, enabled);
    camera_->setControls(&ctrls);
}

void GCamera::setExposure(int32_t exposureUs) {
    ControlList ctrls(camera_->controls());
    ctrls.set(controls::ExposureTime, exposureUs);
    camera_->setControls(&ctrls);
}

void GCamera::setGain(float gain) {
    ControlList ctrls(camera_->controls());
    ctrls.set(controls::AnalogueGain, gain);
    camera_->setControls(&ctrls);
}

// ─────────────────────────────────────────────────────────────────────────────
// onRequestCompleted — called from libcamera's internal thread
// ─────────────────────────────────────────────────────────────────────────────
void GCamera::onRequestCompleted(Request *request) {
    if (request->status() == Request::RequestCancelled) return;
    {
        std::lock_guard<std::mutex> lk(mutex_);
        doneQueue_.push_back(request);
    }
    cv_.notify_one();
}

// ─────────────────────────────────────────────────────────────────────────────
// fillMetadata — extract relevant metadata from a completed request
// ─────────────────────────────────────────────────────────────────────────────
void GCamera::fillMetadata(const ControlList &meta, FrameMetadata &out) {
    if (auto v = meta.get(controls::ExposureTime))
        out.exposureTimeUs = *v;

    if (auto v = meta.get(controls::AnalogueGain))
        out.analogueGain = *v;

    if (auto v = meta.get(controls::DigitalGain))
        out.digitalGain = *v;

    // Black levels: 4 values, one per CFA channel.
    if (auto v = meta.get(controls::SensorBlackLevels)) {
        const auto &bl = *v;
        for (int i = 0; i < 4 && i < static_cast<int>(bl.size()); ++i)
            out.blackLevels[i] = bl[i];
    }

    // Colour correction matrix (3×3, row-major, camera native → sRGB).
    if (auto v = meta.get(controls::ColourCorrectionMatrix)) {
        const auto &ccm = *v;
        if (ccm.size() == 9) {
            for (int i = 0; i < 9; ++i)
                out.colorMatrix[i] = ccm[i];
            out.hasColorMatrix = true;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// captureOne — block until one frame is delivered.
//   out == nullptr  →  frame is discarded (skipBuffers path)
//   returns false on timeout (2 s)
// ─────────────────────────────────────────────────────────────────────────────
bool GCamera::captureOne(RawFrame *out) {
    Request *req = nullptr;
    {
        std::unique_lock<std::mutex> lk(mutex_);
        if (!cv_.wait_for(lk, std::chrono::seconds(2),
                          [this] { return !doneQueue_.empty(); })) {
            std::cerr << "GCamera: timeout waiting for frame\n";
            return false;
        }
        req = doneQueue_.front();
        doneQueue_.pop_front();
    }

    // ── Extract frame data ────────────────────────────────────────────────
    if (out) {
        FrameBuffer *buf = req->buffers().at(rawStream_);
        const FrameBuffer::Plane &plane = buf->planes()[0];

        // mmap the DMA buffer to read the pixel data
        void *mem = mmap(nullptr, plane.length, PROT_READ, MAP_SHARED,
                         plane.fd.get(), plane.offset);
        if (mem == MAP_FAILED) {
            std::cerr << "GCamera: mmap failed\n";
        } else {
            out->data.assign(static_cast<uint8_t *>(mem),
                             static_cast<uint8_t *>(mem) + plane.length);
            munmap(mem, plane.length);
        }

        out->width      = width_;
        out->height     = height_;
        out->stride     = stride_;
        out->cfaPattern = cfaPattern_;

        fillMetadata(req->metadata(), out->metadata);
    }

    // ── Reuse request and requeue ─────────────────────────────────────────
    req->reuse(Request::ReuseBuffers);
    camera_->queueRequest(req);

    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// Public capture interface
// ─────────────────────────────────────────────────────────────────────────────
bool GCamera::skipBuffers(int count) {
    for (int i = 0; i < count; ++i) {
        if (!captureOne(nullptr)) return false;
    }
    return true;
}

bool GCamera::captureRaw(RawFrame &out) {
    return captureOne(&out);
}

bool GCamera::waitExposureChange(int32_t expectedUs, int maxSkip) {
    for (int i = 0; i < maxSkip; ++i) {
        RawFrame frame;
        if (!captureOne(&frame)) return false;
        int32_t got = frame.metadata.exposureTimeUs;
        if (got > 0) {
            float err = std::abs(static_cast<float>(got - expectedUs))
                        / static_cast<float>(expectedUs);
            if (err < 0.1f) {
                std::cout << "GCamera: exposure settled after " << i + 1
                          << " frame(s) (got " << got << " µs)\n";
                return true;
            }
        }
    }
    std::cerr << "GCamera: exposure did not settle within " << maxSkip
              << " frames\n";
    return false;
}
