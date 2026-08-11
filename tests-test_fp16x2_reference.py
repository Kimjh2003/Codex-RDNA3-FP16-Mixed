# 해당코드는 Codex로 수정됨

import math
import struct
import unittest


def half_bits_to_float(bits: int) -> float:
    return struct.unpack("<e", struct.pack("<H", bits & 0xFFFF))[0]


def round_float16(value: float) -> float:
    if math.isnan(value):
        return math.nan
    try:
        return struct.unpack("<e", struct.pack("<e", value))[0]
    except OverflowError:
        return math.copysign(math.inf, value)


def round_float32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def float32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def pack_half2(low_bits: int, high_bits: int) -> int:
    return (low_bits & 0xFFFF) | ((high_bits & 0xFFFF) << 16)


def original_document_expression(packed: int) -> float:
    # unpackHalf2x16 returns FP32 values, so the original multiplication is FP32.
    low = round_float32(half_bits_to_float(packed))
    high = round_float32(half_bits_to_float(packed >> 16))
    low_squared = round_float32(low * low)
    high_squared = round_float32(high * high)
    return round_float32(low_squared + high_squared)


def corrected_mixed_precision_expression(packed: int) -> float:
    low = half_bits_to_float(packed)
    high = half_bits_to_float(packed >> 16)

    # The vector multiply has an FP16 result in the corrected shader.
    low_squared_f16 = round_float16(low * low)
    high_squared_f16 = round_float16(high * high)

    # Each product is promoted before the final FP32 reduction.
    return round_float32(
        round_float32(low_squared_f16) + round_float32(high_squared_f16)
    )


class Fp16x2ReferenceTest(unittest.TestCase):
    def test_known_half_encodings(self) -> None:
        self.assertEqual(half_bits_to_float(0x0000), 0.0)
        self.assertEqual(half_bits_to_float(0x3C00), 1.0)
        self.assertEqual(half_bits_to_float(0xC000), -2.0)
        self.assertTrue(math.isinf(half_bits_to_float(0x7C00)))
        self.assertTrue(math.isnan(half_bits_to_float(0x7E00)))

    def test_exact_pair(self) -> None:
        packed = pack_half2(0x3E00, 0xC000)  # 1.5 and -2.0
        self.assertEqual(corrected_mixed_precision_expression(packed), 6.25)

    def test_original_and_corrected_paths_are_not_the_same_precision(self) -> None:
        packed = pack_half2(0x3C01, 0x0000)
        self.assertNotEqual(
            float32_bits(original_document_expression(packed)),
            float32_bits(corrected_mixed_precision_expression(packed)),
        )

    def test_all_finite_single_lane_patterns(self) -> None:
        for bits in range(1 << 16):
            value = half_bits_to_float(bits)
            if not math.isfinite(value):
                continue

            packed = pack_half2(bits, 0x0000)
            expected = round_float32(round_float16(value * value))
            actual = corrected_mixed_precision_expression(packed)
            self.assertEqual(
                float32_bits(actual),
                float32_bits(expected),
                f"half bits 0x{bits:04x}",
            )


if __name__ == "__main__":
    unittest.main()
