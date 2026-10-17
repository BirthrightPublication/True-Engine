import test from 'node:test';
import assert from 'node:assert/strict';
import {requestDeviceCompat} from '../../sdk/web/webgpu-compat.js';
test('preserves active required limits and original descriptor without global changes',()=>{
  const descriptor={label:'SDK',requiredLimits:{maxInterStageShaderComponents:60,maxBindGroups:4},requiredFeatures:[]};
  let actual;const adapter={limits:{maxBindGroups:4},requestDevice(value){actual=value;return Promise.resolve('actual request');}};
  requestDeviceCompat(adapter,descriptor);
  assert.deepEqual(actual,{label:'SDK',requiredLimits:{maxBindGroups:4},requiredFeatures:[]});
  assert.equal(descriptor.requiredLimits.maxInterStageShaderComponents,60);
  assert.equal(Object.keys(adapter).length,2);
});
test('preserves older WebGPU descriptor verbatim and propagates backend rejection',async()=>{
  const descriptor={requiredLimits:{maxInterStageShaderComponents:60}};
  const failure=new Error('device unavailable');let actual;
  const adapter={limits:{maxInterStageShaderComponents:60},requestDevice(value){actual=value;return Promise.reject(failure);}};
  await assert.rejects(requestDeviceCompat(adapter,descriptor),failure);assert.equal(actual,descriptor);
});
