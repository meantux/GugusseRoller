#pragma once

#include "GCamera.h"
#include <string>

// ─────────────────────────────────────────────────────────────────────────────
// DngWriter — writes a RawFrame as a 12-bit packed DNG file using libtiff.
//
// The raw data from libcamera is in SBGGR12_CSI2P (Sony CSI-2 packed) format:
//   2 pixels → 3 bytes:  [P0hi][P1hi][P1lo|P0lo]
//
// DNG/TIFF standard 12-bit packing (MSB-first) is different:
//   2 pixels → 3 bytes:  [P0hi][P0lo|P1hi][P1lo]
//
// DngWriter converts each row on the fly before writing, so no second full
// frame buffer is needed — only a single row buffer (~6 KB) is allocated.
//
// Custom DNG tags are registered once via a libtiff extender and then written
// normally with TIFFSetField.
//
// For the future per-channel bracketing feature:
//   The caller performs channel splicing on the RawFrame (still in CSI2P
//   format) before calling write().  The splice operates directly on the
//   packed bytes without unpacking, using the fixed byte positions of each
//   Bayer channel within a CSI2P triplet.
// ─────────────────────────────────────────────────────────────────────────────
class DngWriter {
public:
    // Write frame to path (written to path + ".tmp", then renamed atomically).
    // Returns true on success.
    static bool write(const std::string &path, const RawFrame &frame);

private:
    // Register DNG-specific TIFF tags with the libtiff extender.
    // Called once before the first TIFF is opened.
    static void ensureTagsRegistered();

    // Convert one row from CSI2P packing to TIFF-standard 12-bit packing.
    // src and dst must each be (width * 3 / 2) bytes.
    // width must be even.
    static void convertRowCsi2pToTiff12(const uint8_t *src,
                                        uint8_t       *dst,
                                        uint32_t       width);

    // 4-byte CFA pattern for a given CfaPattern, in DNG byte order:
    //   [0]=R row/col, [1]=G, [2]=G, [3]=B  (positions within 2×2 block)
    static void cfaBytes(CfaPattern pattern, uint8_t out[4]);

    static bool tagsRegistered_;
};
