#include "DngWriter.h"

#include <tiffio.h>

#include <chrono>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>

// ─────────────────────────────────────────────────────────────────────────────
// DNG tag numbers not defined in stock tiffio.h
// ─────────────────────────────────────────────────────────────────────────────
#ifndef PHOTOMETRIC_CFA
#define PHOTOMETRIC_CFA 32803
#endif

#define TIFFTAG_DNGVERSION              50706
#define TIFFTAG_DNGBACKWARDVERSION      50707
#define TIFFTAG_UNIQUECAMERAMODEL       50708
#define TIFFTAG_BLACKLEVEL              50717
#define TIFFTAG_WHITELEVEL              50718
#define TIFFTAG_COLORMATRIX1            50721
#define TIFFTAG_CALIBRATIONILLUMINANT1  50778

// FIELD_CUSTOM is an internal libtiff value (65 on libtiff 4.x).
// We define it here only if the header does not expose it.
#ifndef FIELD_CUSTOM
#define FIELD_CUSTOM 65
#endif

// ─────────────────────────────────────────────────────────────────────────────
// Custom tag registration — called once via TIFFSetTagExtender
// ─────────────────────────────────────────────────────────────────────────────
bool DngWriter::tagsRegistered_ = false;

static TIFFExtendProc parentExtender_ = nullptr;

static const TIFFFieldInfo dngFieldInfo[] = {
    // DNGVersion: 4 bytes, e.g. {1,4,0,0}
    { TIFFTAG_DNGVERSION, 4, 4, TIFF_BYTE, FIELD_CUSTOM,
      1, 0, const_cast<char *>("DNGVersion") },
    // DNGBackwardVersion: 4 bytes
    { TIFFTAG_DNGBACKWARDVERSION, 4, 4, TIFF_BYTE, FIELD_CUSTOM,
      1, 0, const_cast<char *>("DNGBackwardVersion") },
    // UniqueCameraModel: ASCII string
    { TIFFTAG_UNIQUECAMERAMODEL, -1, -1, TIFF_ASCII, FIELD_CUSTOM,
      1, 0, const_cast<char *>("UniqueCameraModel") },
    // BlackLevel: 4 RATIONAL values (one per CFA channel), variable count
    { TIFFTAG_BLACKLEVEL, -1, -1, TIFF_RATIONAL, FIELD_CUSTOM,
      1, 1, const_cast<char *>("BlackLevel") },
    // WhiteLevel: 1 LONG, variable count (one per sample)
    { TIFFTAG_WHITELEVEL, -1, -1, TIFF_LONG, FIELD_CUSTOM,
      1, 1, const_cast<char *>("WhiteLevel") },
    // ColorMatrix1: 9 SRATIONAL values (3×3 matrix)
    { TIFFTAG_COLORMATRIX1, -1, -1, TIFF_SRATIONAL, FIELD_CUSTOM,
      1, 1, const_cast<char *>("ColorMatrix1") },
    // CalibrationIlluminant1: 1 SHORT  (21 = D65)
    { TIFFTAG_CALIBRATIONILLUMINANT1, 1, 1, TIFF_SHORT, FIELD_CUSTOM,
      1, 0, const_cast<char *>("CalibrationIlluminant1") },
};

static void dngTagExtender(TIFF *tif) {
    TIFFMergeFieldInfo(tif, dngFieldInfo,
                       sizeof(dngFieldInfo) / sizeof(dngFieldInfo[0]));
    if (parentExtender_)
        (*parentExtender_)(tif);
}

void DngWriter::ensureTagsRegistered() {
    if (tagsRegistered_) return;
    parentExtender_ = TIFFSetTagExtender(dngTagExtender);
    tagsRegistered_ = true;
}

// ─────────────────────────────────────────────────────────────────────────────
// convertRowCsi2pToTiff12
//
// CSI2P layout per pair:   [P0[11:4]] [P1[11:4]] [P1[3:0]|P0[3:0]]
// TIFF 12-bit layout:      [P0[11:4]] [P0[3:0]|P1[11:8]] [P1[7:0]]
// ─────────────────────────────────────────────────────────────────────────────
void DngWriter::convertRowCsi2pToTiff12(const uint8_t *src,
                                         uint8_t       *dst,
                                         uint32_t       width) {
    uint32_t pairs = width / 2;
    for (uint32_t i = 0; i < pairs; ++i, src += 3, dst += 3) {
        uint32_t p0 = (static_cast<uint32_t>(src[0]) << 4) | (src[2] & 0x0Fu);
        uint32_t p1 = (static_cast<uint32_t>(src[1]) << 4) | (src[2] >> 4);
        dst[0] = static_cast<uint8_t>(p0 >> 4);
        dst[1] = static_cast<uint8_t>(((p0 & 0x0Fu) << 4) | (p1 >> 8));
        dst[2] = static_cast<uint8_t>(p1 & 0xFFu);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// cfaBytes — DNG CFAPattern byte values for a given CfaPattern
//
// DNG CFAPattern encodes the color at each position in the repeating 2×2 tile:
//   [row0col0, row0col1, row1col0, row1col1]
//   0=R, 1=G, 2=B
// ─────────────────────────────────────────────────────────────────────────────
void DngWriter::cfaBytes(CfaPattern pattern, uint8_t out[4]) {
    switch (pattern) {
        case CfaPattern::RGGB: out[0]=0; out[1]=1; out[2]=1; out[3]=2; break;
        case CfaPattern::GRBG: out[0]=1; out[1]=0; out[2]=2; out[3]=1; break;
        case CfaPattern::GBRG: out[0]=1; out[1]=2; out[2]=0; out[3]=1; break;
        case CfaPattern::BGGR: // fall-through — most common on IMX477
        default:               out[0]=2; out[1]=1; out[2]=1; out[3]=0; break;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// write()
// ─────────────────────────────────────────────────────────────────────────────
bool DngWriter::write(const std::string &path, const RawFrame &frame) {
    ensureTagsRegistered();

    std::string tmp = path + ".tmp";
    TIFF *tif = TIFFOpen(tmp.c_str(), "w");
    if (!tif) {
        std::cerr << "DngWriter: cannot open " << tmp << "\n";
        return false;
    }

    const uint32_t w        = frame.width;
    const uint32_t h        = frame.height;
    const uint32_t rowBytes = (w * 3) / 2;   // 12-bit packed: 1.5 bytes/pixel

    // ── Standard TIFF tags ────────────────────────────────────────────────

    TIFFSetField(tif, TIFFTAG_IMAGEWIDTH,      w);
    TIFFSetField(tif, TIFFTAG_IMAGELENGTH,     h);
    TIFFSetField(tif, TIFFTAG_BITSPERSAMPLE,   (uint16_t)12);
    TIFFSetField(tif, TIFFTAG_SAMPLESPERPIXEL, (uint16_t)1);
    TIFFSetField(tif, TIFFTAG_COMPRESSION,     (uint16_t)COMPRESSION_NONE);
    TIFFSetField(tif, TIFFTAG_PHOTOMETRIC,     (uint16_t)PHOTOMETRIC_CFA);
    TIFFSetField(tif, TIFFTAG_PLANARCONFIG,    (uint16_t)PLANARCONFIG_CONTIG);
    TIFFSetField(tif, TIFFTAG_ROWSPERSTRIP,    h);   // single strip
    TIFFSetField(tif, TIFFTAG_ORIENTATION,     (uint16_t)ORIENTATION_TOPLEFT);
    TIFFSetField(tif, TIFFTAG_MAKE,            "Raspberry Pi");
    TIFFSetField(tif, TIFFTAG_MODEL,           "IMX477");
    TIFFSetField(tif, TIFFTAG_SOFTWARE,        "GugusseRoller");

    // DateTime
    {
        auto now = std::chrono::system_clock::now();
        std::time_t t = std::chrono::system_clock::to_time_t(now);
        std::tm tm_buf;
        localtime_r(&t, &tm_buf);
        char buf[20];
        strftime(buf, sizeof(buf), "%Y:%m:%d %H:%M:%S", &tm_buf);
        TIFFSetField(tif, TIFFTAG_DATETIME, buf);
    }

    // ExposureTime as a rational (numerator = µs, denominator = 1 000 000)
    if (frame.metadata.exposureTimeUs > 0) {
        TIFFSetField(tif, TIFFTAG_EXPOSURETIME,
                     static_cast<float>(frame.metadata.exposureTimeUs) / 1e6f);
    }

    // ── CFA tags ─────────────────────────────────────────────────────────

    uint16_t cfaDim[2] = {2, 2};
    TIFFSetField(tif, TIFFTAG_CFAREPEATPATTERNDIM, cfaDim);

    uint8_t cfaPat[4];
    cfaBytes(frame.cfaPattern, cfaPat);
    TIFFSetField(tif, TIFFTAG_CFAPATTERN, 4, cfaPat);

    // ── DNG-specific tags ─────────────────────────────────────────────────

    static const uint8_t dngVersion[4]         = {1, 4, 0, 0};
    static const uint8_t dngBackwardVersion[4]  = {1, 1, 0, 0};
    TIFFSetField(tif, TIFFTAG_DNGVERSION,         dngVersion);
    TIFFSetField(tif, TIFFTAG_DNGBACKWARDVERSION, dngBackwardVersion);
    TIFFSetField(tif, TIFFTAG_UNIQUECAMERAMODEL,
                 "Raspberry Pi High Quality Camera");

    // CalibrationIlluminant1 = 21 (D65)
    TIFFSetField(tif, TIFFTAG_CALIBRATIONILLUMINANT1, (uint16_t)21);

    // WhiteLevel = 4095  (12-bit max)
    {
        uint32_t wl = 4095;
        TIFFSetField(tif, TIFFTAG_WHITELEVEL, 1, &wl);
    }

    // BlackLevel — 4 values (one per CFA channel), stored as RATIONAL
    // TIFFFieldInfo with TIFF_RATIONAL and passcount=1 expects:
    //   (count, float*) where each float represents the rational value.
    // libtiff internally converts float → {num, den} for RATIONAL fields.
    {
        float bl[4];
        for (int i = 0; i < 4; ++i)
            bl[i] = static_cast<float>(frame.metadata.blackLevels[i]);
        TIFFSetField(tif, TIFFTAG_BLACKLEVEL, 4, bl);
    }

    // ColorMatrix1 — 3×3 SRATIONAL matrix, stored as pairs of int32_t.
    // Scale floats to integer rationals with denominator 10000.
    {
        // Fallback IMX477 matrix (D65, from libcamera tuning reference).
        // If available, prefer the per-frame CCM from metadata.
        const float *src = nullptr;
        static const float fallback[9] = {
             1.9435f, -1.0992f,  0.1556f,
            -0.1790f,  1.5915f, -0.4124f,
             0.0139f, -0.2999f,  1.2860f,
        };
        if (frame.metadata.hasColorMatrix)
            src = frame.metadata.colorMatrix;
        else
            src = fallback;

        // SRATIONAL is stored as pairs: {int32_t numerator, int32_t denom}
        int32_t matrix[18];
        for (int i = 0; i < 9; ++i) {
            matrix[i * 2 + 0] = static_cast<int32_t>(src[i] * 10000.0f);
            matrix[i * 2 + 1] = 10000;
        }
        TIFFSetField(tif, TIFFTAG_COLORMATRIX1, 9, matrix);
    }

    // ── Pixel data — convert row by row from CSI2P to TIFF 12-bit ────────

    std::vector<uint8_t> rowBuf(rowBytes);

    // Collect into one strip to minimise IFD overhead.
    std::vector<uint8_t> stripData;
    stripData.reserve(rowBytes * h);

    for (uint32_t row = 0; row < h; ++row) {
        const uint8_t *srcRow = frame.data.data() + row * frame.stride;
        convertRowCsi2pToTiff12(srcRow, rowBuf.data(), w);
        stripData.insert(stripData.end(), rowBuf.begin(), rowBuf.end());
    }

    if (TIFFWriteRawStrip(tif, 0, stripData.data(),
                          static_cast<tmsize_t>(stripData.size())) < 0) {
        std::cerr << "DngWriter: TIFFWriteRawStrip failed\n";
        TIFFClose(tif);
        std::filesystem::remove(tmp);
        return false;
    }

    TIFFClose(tif);

    // Atomic rename
    std::error_code ec;
    std::filesystem::rename(tmp, path, ec);
    if (ec) {
        std::cerr << "DngWriter: rename failed: " << ec.message() << "\n";
        std::filesystem::remove(tmp);
        return false;
    }

    std::cout << "DngWriter: wrote " << path
              << " (" << stripData.size() / 1024 << " KB)\n";
    return true;
}
