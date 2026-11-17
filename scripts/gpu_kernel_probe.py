"""Actual CUDA driver JIT/kernel check. No torch, nvcc, downloads or paid services.
Run in a GPU-enabled existing Python container, e.g. the Blender image.
"""
import ctypes as C
import json


def probe():
    cuda=C.CDLL('libcuda.so.1')
    def check(code):
        if code:
            message=C.c_char_p()
            cuda.cuGetErrorString(code,C.byref(message))
            raise RuntimeError(f'CUDA error {code}: {message.value.decode() if message.value else "unknown"}')
    check(cuda.cuInit(0))
    count=C.c_int();check(cuda.cuDeviceGetCount(C.byref(count)))
    if count.value<1:raise RuntimeError('No CUDA devices')
    device=C.c_int();check(cuda.cuDeviceGet(C.byref(device),0))
    name=C.create_string_buffer(256);check(cuda.cuDeviceGetName(name,len(name),device))
    context=C.c_void_p();check(cuda.cuCtxCreate_v2(C.byref(context),0,device))
    module=C.c_void_p();memory=C.c_uint64()
    ptx=b'''.version 8.0
.target sm_75
.address_size 64
.visible .entry write_answer(.param .u64 destination) {
 .reg .b64 address;
 .reg .b32 value;
 ld.param.u64 address,[destination];
 mov.u32 value,42;
 st.global.u32 [address],value;
 ret;
}
'''
    try:
        check(cuda.cuMemAlloc_v2(C.byref(memory),C.c_size_t(4)))
        check(cuda.cuModuleLoadData(C.byref(module),C.c_char_p(ptx)))
        function=C.c_void_p();check(cuda.cuModuleGetFunction(C.byref(function),module,b'write_answer'))
        pointer=C.c_uint64(memory.value);arguments=(C.c_void_p*1)(C.cast(C.byref(pointer),C.c_void_p))
        check(cuda.cuLaunchKernel(function,1,1,1,1,1,1,0,None,arguments,None))
        check(cuda.cuCtxSynchronize())
        result=C.c_int();check(cuda.cuMemcpyDtoH_v2(C.byref(result),memory,C.c_size_t(4)))
        if result.value!=42:raise RuntimeError(f'GPU kernel returned {result.value}, expected 42')
        return {'status':'passed','device':name.value.decode(),'device_count':count.value,'kernel_result':result.value}
    finally:
        if memory.value:cuda.cuMemFree_v2(memory)
        if module.value:cuda.cuModuleUnload(module)
        cuda.cuCtxDestroy_v2(context)


if __name__=='__main__':print(json.dumps(probe(),indent=2))
