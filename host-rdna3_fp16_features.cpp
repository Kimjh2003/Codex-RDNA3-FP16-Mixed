// 해당코드는 Codex로 수정됨

#include <cstdint>
#include <stdexcept>
#include <vulkan/vulkan.h>

VkDevice createFp16Device(
    VkPhysicalDevice physicalDevice,
    const VkDeviceQueueCreateInfo* queueCreateInfos,
    std::uint32_t queueCreateInfoCount)
{
    VkPhysicalDeviceShaderFloat16Int8Features supportedFloat16{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT16_INT8_FEATURES};
    VkPhysicalDeviceFeatures2 supportedFeatures{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
    supportedFeatures.pNext = &supportedFloat16;

    vkGetPhysicalDeviceFeatures2(physicalDevice, &supportedFeatures);
    if (supportedFloat16.shaderFloat16 != VK_TRUE)
    {
        throw std::runtime_error("shaderFloat16 is unavailable");
    }

    VkPhysicalDeviceShaderFloat16Int8Features requestedFloat16{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT16_INT8_FEATURES};
    requestedFloat16.shaderFloat16 = VK_TRUE;

    VkDeviceCreateInfo createInfo{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    createInfo.pNext = &requestedFloat16;
    createInfo.queueCreateInfoCount = queueCreateInfoCount;
    createInfo.pQueueCreateInfos = queueCreateInfos;
    createInfo.pEnabledFeatures = nullptr;

    VkDevice device = VK_NULL_HANDLE;
    const VkResult result = vkCreateDevice(physicalDevice, &createInfo, nullptr, &device);
    if (result != VK_SUCCESS)
    {
        throw std::runtime_error("vkCreateDevice failed for FP16 device");
    }

    return device;
}
