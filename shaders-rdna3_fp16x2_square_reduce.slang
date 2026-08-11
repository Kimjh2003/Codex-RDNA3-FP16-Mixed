// 해당코드는 Codex로 수정됨

[[vk::binding(0, 0)]]
StructuredBuffer<uint32_t> packedData;

[[vk::binding(1, 0)]]
RWStructuredBuffer<float> resultData;

struct DispatchInfo
{
    uint32_t elementCount;
};

[[vk::push_constant]]
ConstantBuffer<DispatchInfo> dispatchInfo;

[shader("compute")]
[numthreads(256, 1, 1)]
void main(uint3 dispatchThreadID : SV_DispatchThreadID)
{
    uint32_t idx = dispatchThreadID.x;
    if (idx >= dispatchInfo.elementCount)
    {
        return;
    }

    uint32_t packed = packedData[idx];

    // Interpret both 16-bit halves, then explicitly narrow to half2 before
    // multiplication. The generated SPIR-V uses OpFMul with a v2half result.
    float2 unpackedF32 = float2(
        f16tof32(packed & 0xffffu),
        f16tof32(packed >> 16u));
    half2 valuesF16 = half2(unpackedF32);
    half2 squaredF16 = valuesF16 * valuesF16;

    // Convert each FP16 product to FP32 before the reduction.
    resultData[idx] = float(squaredF16.x) + float(squaredF16.y);
}
