/** wgpu 0.19 names a limit retired by current WebGPU. Keep every active limit
 * and call the actual adapter. No prototype/global patch or renderer substitute.
 */
export function requestDeviceCompat(adapter, descriptor) {
  if ('maxInterStageShaderComponents' in adapter.limits || !descriptor.requiredLimits) {
    return adapter.requestDevice(descriptor);
  }
  const {maxInterStageShaderComponents: retired, ...requiredLimits} = descriptor.requiredLimits;
  void retired;
  return adapter.requestDevice({...descriptor, requiredLimits});
}
