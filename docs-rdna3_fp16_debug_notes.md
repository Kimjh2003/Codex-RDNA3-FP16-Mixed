# RDNA3 FP16x2 square + FP32 reduction debugging notes

> 해당코드는 Codex로 수정됨

## 원본에서 확인된 문제

1. GLSL의 `unpackHalf2x16()` 반환 타입은 FP32 `vec2`다. 따라서 원본의 `vec2 computed_f16 = unpacked_f16 * unpacked_f16;`은 이름과 달리 FP32 곱셈이다.
2. `GL_EXT_shader_16bit_storage`는 실제로 16비트 값을 인터페이스 저장소에 넣을 때 필요한 확장이다. 수정본은 packed 값을 `uint`로 보관하고 FP16을 함수 내부 산술에만 사용하므로 이 확장을 요구하지 않는다.
3. 원본은 subgroup 연산을 사용하지 않으므로 `GL_KHR_shader_subgroup_arithmetic`도 필요하지 않다.
4. `shaderFloat16`은 Vulkan 1.4에서도 무조건 사용할 수 있다고 가정하면 안 된다. `vkGetPhysicalDeviceFeatures2`로 지원 여부를 질의한 뒤 `VkDeviceCreateInfo::pNext`에서 활성화해야 한다.
5. 원본에는 디스패치 범위 검사가 없다. 수정본은 push constant의 `elementCount`를 검사한다.
6. SPIR-V에 2×FP16 `OpFMul`이 있어도 RDNA3 packed FP16 명령 사용을 보장하지 않는다. 최종 명령 선택은 드라이버가 결정한다.

## 수정된 연산 순서

입력 `uint` 하나에는 IEEE 754 binary16 값 두 개가 들어 있다.

```text
packed uint32
  -> FP16 비트 두 개 해석
  -> half2/f16vec2로 명시적 축소
  -> FP16 벡터 제곱
  -> 각 결과를 FP32로 승격
  -> FP32 덧셈
  -> FP32 출력
```

이 예시는 FP16 곱셈과 FP32 reduction을 순서대로 수행하는 혼합 정밀도 코드다. FP32와 FP16 유닛의 물리적 동시 실행을 증명하는 코드는 아니다.

## 필요한 Vulkan 기능

`host-rdna3_fp16_features.cpp`는 아래 기능을 질의하고 활성화한다.

```cpp
VkPhysicalDeviceShaderFloat16Int8Features supportedFloat16{
    VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT16_INT8_FEATURES};
VkPhysicalDeviceFeatures2 supportedFeatures{
    VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
supportedFeatures.pNext = &supportedFloat16;
vkGetPhysicalDeviceFeatures2(physicalDevice, &supportedFeatures);

if (!supportedFloat16.shaderFloat16) {
    throw std::runtime_error("shaderFloat16 is unavailable");
}
```

버퍼는 `uint32_t`와 FP32만 저장하므로 이 설계에는 `storageBuffer16BitAccess`가 필요하지 않다. FP16 값을 StorageBuffer에 직접 넣는 설계로 바꾸면 별도의 16비트 저장소 기능을 질의해야 한다.

## 검증 방법

```powershell
slangc shaders-rdna3_fp16x2_square_reduce.slang `
  -entry main -stage compute -target spirv `
  -profile spirv_1_6 -o rdna3_fp16x2_square_reduce.spv

slangc shaders-rdna3_fp16x2_square_reduce.slang `
  -entry main -stage compute -target spirv-asm `
  -profile spirv_1_6 -o rdna3_fp16x2_square_reduce.spv-asm

Select-String -Path rdna3_fp16x2_square_reduce.spv-asm `
  -Pattern 'OpCapability Float16','OpTypeFloat 16','OpFMul %v2half'

python tests-test_fp16x2_reference.py
```

검증한 SPIR-V에는 다음 특성이 존재한다.

- SPIR-V 버전 1.6
- `OpCapability Float16`
- 16비트 `OpTypeFloat`
- `OpFMul` 결과 타입 `v2half`
- FP16 결과를 FP32로 바꾸는 `OpFConvert`

실제 RDNA3 ISA는 Radeon GPU Analyzer 또는 드라이버의 파이프라인 실행 파일 조회 기능으로 확인해야 한다.

## 공식 참고 문서

- [VkPhysicalDeviceShaderFloat16Int8Features](https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceShaderFloat16Int8Features.html)
- [VK_KHR_shader_float16_int8](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_shader_float16_int8.html)
- [GL_EXT_shader_explicit_arithmetic_types](https://docs.vulkan.org/glslext/latest/glslext/ext/GL_EXT_shader_explicit_arithmetic_types.html)
- [Using explicit 16-bit arithmetic in applications](https://docs.vulkan.org/samples/latest/samples/performance/16bit_arithmetic/README.html)
- [SPIR-V specification](https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html)
