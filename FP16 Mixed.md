# RDNA3 FP16x2 square + FP32 reduction

> 해당코드는 Codex로 수정됨

`AMD RDNA3 FP32 16bit 중첩연산 예시.pdf`의 아이디어를 실제 FP16 산술이 SPIR-V에 남는 형태로 수정한 예시입니다.

원본의 `unpackHalf2x16()`은 packed FP16 두 개를 FP32 `vec2`로 반환합니다. 따라서 원본의 `vec2 * vec2`는 변수명과 달리 FP16 곱셈을 보장하지 않습니다. 수정본은 값을 명시적으로 `half2`/`f16vec2`로 변환한 뒤 제곱하고, 각 FP16 결과를 FP32로 승격해 합산합니다.

## 파일

- [`shaders-rdna3_fp16x2_square_reduce.slang`](shaders-rdna3_fp16x2_square_reduce.slang): SPIR-V 1.6 출력을 검증한 기준 구현
- [`shaders-rdna3_fp16x2_square_reduce.comp`](shaders-rdna3_fp16x2_square_reduce.comp): Vulkan GLSL 대응본
- [`host-rdna3_fp16_features.cpp`](host-rdna3_fp16_features.cpp): `shaderFloat16` 질의 및 활성화 예시
- [`tests-test_fp16x2_reference.py`](tests-test_fp16x2_reference.py): FP16 반올림과 FP32 합산 기준 테스트
- [`docs-rdna3_fp16_debug_notes.md`](docs-rdna3_fp16_debug_notes.md): 문제 원인, 요구 기능, 검증 절차

기준 Slang 셰이더에서는 SPIR-V 1.6의 `Float16` capability, 16비트 부동소수점 타입, `OpFMul`의 `v2half` 결과를 확인했습니다. 실제 RDNA3 packed FP16 기계 명령 선택 여부는 드라이버가 생성한 ISA를 별도로 확인해야 합니다.
