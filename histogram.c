#include <stdint.h>
#include <stddef.h>

void histogram_rgb8(const uint8_t *data, size_t pixel_count,
                    uint32_t *hist_r, uint32_t *hist_g, uint32_t *hist_b) {
    for (size_t i = 0; i < pixel_count; ++i) {
        hist_r[data[3 * i]]++;
        hist_g[data[3 * i + 1]]++;
        hist_b[data[3 * i + 2]]++;
    }
}

void histogram_gray12(const uint8_t *data, size_t byte_count, uint32_t *hist) {
    size_t i = 0;
    while (i + 2 < byte_count) {
        uint16_t p0 = data[i] | ((data[i + 1] & 0x0F) << 8);
        uint16_t p1 = (data[i + 1] >> 4) | (data[i + 2] << 4);
        hist[p0]++;
        hist[p1]++;
        i += 3;
    }
}
