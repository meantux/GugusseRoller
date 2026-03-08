#pragma once

#include <libcamera/libcamera.h>

#include <condition_variable>
#include <cstdint>
#include <deque>
#include <mutex>
#include <vector>

// ─────────────────────────────────────────────────────────────────────────────
// CfaPattern — matches libcamera's draft::ColorFilterArrangement values
// ─────────────────────────────────────────────────────────────────────────────
enum class CfaPattern : uint8_t {
    RGGB = 0,
    GRBG = 1,
    GBRG = 2,
    BGGR = 3,
    Mono = 4,
};

// ─────────────────────────────────────────────────────────────────────────────
// FrameMetadata — subset of libcamera metadata we care about for DNG writing
// ─────────────────────────────────────────────────────────────────────────────
struct FrameMetadata {
    int32_t exposureTimeUs = 0;
    float   analogueGain   = 1.0f;
    float   digitalGain    = 1.0f;

    // Black level, one value per CFA channel (BGGR order).
    // IMX477 default is 256 for all channels.
    int32_t blackLevels[4] = {256, 256, 256, 256};

    // 3×3 colour correction matrix (row-major), camera native → sRGB.
    // Used as ColorMatrix1 in the DNG (matches what picamera2 does).
    // hasColorMatrix is false when libcamera did not provide it.
    float colorMatrix[9]  = {};
    bool  hasColorMatrix  = false;
};

// ─────────────────────────────────────────────────────────────────────────────
// RawFrame — one captured raw Bayer frame
//
// data    : raw bytes from libcamera, in SBGGR12_CSI2P packing.
//           Each row is `stride` bytes; only (width * 3 / 2) bytes per row
//           contain valid pixel data — the remainder is libcamera alignment
//           padding that must be skipped when writing.
// ─────────────────────────────────────────────────────────────────────────────
struct RawFrame {
    std::vector<uint8_t> data;
    uint32_t             width      = 0;
    uint32_t             height     = 0;
    uint32_t             stride     = 0;   // bytes per row including padding
    CfaPattern           cfaPattern = CfaPattern::BGGR;
    FrameMetadata        metadata;
};

// ─────────────────────────────────────────────────────────────────────────────
// GCamera — synchronous wrapper around the libcamera C++ API
//
// Usage:
//   GCamera::Config cfg;  cfg.fps = 10;
//   GCamera cam(cfg);
//   cam.start();
//   cam.setAeEnabled(false);
//   cam.setExposure(40000);
//   cam.setGain(1.0f);
//   cam.skipBuffers(3);           // let camera settle
//   RawFrame frame;
//   cam.captureRaw(frame);
//   cam.stop();
// ─────────────────────────────────────────────────────────────────────────────
class GCamera {
public:
    struct Config {
        int  fps   = 10;
        bool hflip = false;
        bool vflip = false;
    };

    explicit GCamera(const Config &cfg);
    ~GCamera();

    GCamera(const GCamera &) = delete;
    GCamera &operator=(const GCamera &) = delete;

    bool start();
    void stop();

    // Camera controls — call after start().
    // Controls take effect on subsequent captures; skipBuffers() lets the
    // pipeline drain stale frames after a change.
    void setAeEnabled(bool enabled);
    void setExposure(int32_t exposureUs);
    void setGain(float analogueGain);

    // Capture helpers
    bool skipBuffers(int count);
    bool captureRaw(RawFrame &out);

    // Drain frames until the reported ExposureTime metadata is within 10% of
    // expected, or maxSkip frames have been discarded (same logic as Python).
    bool waitExposureChange(int32_t expectedUs, int maxSkip = 24);

    uint32_t   width()      const { return width_; }
    uint32_t   height()     const { return height_; }
    uint32_t   stride()     const { return stride_; }
    CfaPattern cfaPattern() const { return cfaPattern_; }

private:
    // Called from libcamera's internal thread — must be fast and lock-free
    // except for the handoff mutex.
    void onRequestCompleted(libcamera::Request *request);

    // Block until one frame is ready.  If out == nullptr the frame is
    // discarded (used by skipBuffers).  Returns false on timeout or error.
    bool captureOne(RawFrame *out);

    void fillMetadata(const libcamera::ControlList &meta, FrameMetadata &out);

    Config cfg_;

    std::unique_ptr<libcamera::CameraManager>        manager_;
    std::shared_ptr<libcamera::Camera>               camera_;
    std::unique_ptr<libcamera::CameraConfiguration>  camConfig_;
    libcamera::Stream                               *rawStream_ = nullptr;

    std::unique_ptr<libcamera::FrameBufferAllocator> allocator_;
    // Small pool of requests for double-buffering
    std::vector<std::unique_ptr<libcamera::Request>> requests_;

    // Producer side: camera thread pushes completed requests here.
    // Consumer side: captureOne() pops from here.
    std::deque<libcamera::Request *> doneQueue_;
    std::mutex                       mutex_;
    std::condition_variable          cv_;

    bool running_ = false;

    // Derived from stream config after configure()
    uint32_t   width_      = 0;
    uint32_t   height_     = 0;
    uint32_t   stride_     = 0;
    CfaPattern cfaPattern_ = CfaPattern::BGGR;
};
