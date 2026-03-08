#include "GCamera.h"
#include "DngWriter.h"

#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <iomanip>
#include <iostream>

// ─────────────────────────────────────────────────────────────────────────────
// Standalone test: initialise camera, capture one DNG, report timing.
//
// Build:
//   cd cpp && cmake -B build && cmake --build build
//
// Run on the Pi:
//   ./build/camera_test [output.dng]
//
// Verify with:
//   exiftool output.dng
//   darktable output.dng   (or RawTherapee)
// ─────────────────────────────────────────────────────────────────────────────
int main(int argc, char *argv[]) {
    std::string outPath = (argc > 1) ? argv[1] : "/dev/shm/test.dng";

    std::cout << "── GugusseRoller camera_test ───────────────────────\n";
    std::cout << "Output: " << outPath << "\n\n";

    // ── Init camera ───────────────────────────────────────────────────────
    GCamera::Config cfg;
    cfg.fps   = 10;
    cfg.hflip = false;
    cfg.vflip = false;

    GCamera cam(cfg);
    if (!cam.start()) {
        std::cerr << "Failed to start camera\n";
        return EXIT_FAILURE;
    }

    // ── Fix exposure and gain (AE off, 40 ms, gain 1.0) ──────────────────
    cam.setAeEnabled(false);
    cam.setExposure(40000);
    cam.setGain(1.0f);

    // Drain stale frames so controls take effect before we measure.
    std::cout << "Skipping 5 frames to let controls settle...\n";
    cam.skipBuffers(5);

    // Wait until the reported exposure is within 10% of 40 ms.
    cam.waitExposureChange(40000);

    // ── Capture ───────────────────────────────────────────────────────────
    std::cout << "\nCapturing raw frame...\n";
    auto t0 = std::chrono::steady_clock::now();

    RawFrame frame;
    if (!cam.captureRaw(frame)) {
        std::cerr << "Capture failed\n";
        cam.stop();
        return EXIT_FAILURE;
    }

    auto t1 = std::chrono::steady_clock::now();
    double captureMs = std::chrono::duration<double, std::milli>(t1 - t0).count();

    std::cout << "  size:      " << frame.width << " × " << frame.height << "\n";
    std::cout << "  stride:    " << frame.stride << " bytes\n";
    std::cout << "  CFA:       " << static_cast<int>(frame.cfaPattern) << "\n";
    std::cout << "  exposure:  " << frame.metadata.exposureTimeUs << " µs\n";
    std::cout << "  gain:      " << frame.metadata.analogueGain << "\n";
    std::cout << "  blackLvl:  "
              << frame.metadata.blackLevels[0] << " "
              << frame.metadata.blackLevels[1] << " "
              << frame.metadata.blackLevels[2] << " "
              << frame.metadata.blackLevels[3] << "\n";
    std::cout << "  CCM avail: " << (frame.metadata.hasColorMatrix ? "yes" : "no") << "\n";
    std::cout << "  capture:   " << std::fixed << std::setprecision(1)
              << captureMs << " ms\n\n";

    cam.stop();

    // ── Write DNG ─────────────────────────────────────────────────────────
    // Ensure output directory exists.
    auto outDir = std::filesystem::path(outPath).parent_path();
    if (!outDir.empty())
        std::filesystem::create_directories(outDir);

    std::cout << "Writing DNG...\n";
    auto t2 = std::chrono::steady_clock::now();

    bool ok = DngWriter::write(outPath, frame);

    auto t3 = std::chrono::steady_clock::now();
    double writeMs = std::chrono::duration<double, std::milli>(t3 - t2).count();

    if (!ok) {
        std::cerr << "DNG write failed\n";
        return EXIT_FAILURE;
    }

    auto fileSize = std::filesystem::file_size(outPath);
    std::cout << "  write:     " << std::fixed << std::setprecision(1)
              << writeMs << " ms\n";
    std::cout << "  file size: " << fileSize / (1024 * 1024) << " MB ("
              << fileSize / 1024 << " KB)\n";
    std::cout << "\nDone. Verify with: exiftool " << outPath << "\n";

    return EXIT_SUCCESS;
}
