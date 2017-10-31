

Develop cuda program in windows:
1) visual studio 2015, 
2) developer command prompt
   cd e:\proj\gputest
3) nvcc test.cu
4) a.exe

concepts
SM: streaming multiprocessor

GPU
Warp  32 threads group.

SIMT  single instruction, multiple threads

A warp executes one common instruction at a time.

SIMD  single instruction, multiple data

PTX ISA
a low-level Parallel Thread eXecution virtual machine 
ISA instruction architecture

CTA - cooperative thread array

thread block: a maximum of 1024 threads. threads in one block is expected to reside on the same core.
Does a gpu kernel function call uses stack?

Column major matrix vs row major matrix

Kernels: a function to tun in device

GPU names: sm_xy, where x is gpu generation number, y is version in this generation.

questions
Q:shared memory is shared inside a thread block. a block of threads are scheduled inside one SM?
Q: is A calls B in device, will A wait B? kernel invoking is asynchronous?
thread arch
 grid -> block -> thread

Q: how is a warp scheduled?
Memory arch
 global
 Shared memory: on-chip, higher bandwidth and lower latency.
 Local memory
 thread-local
 texture
 Constant
 registers

Managed memory: 

Q:shared memory is shared inside a thread block, how is it implemented?
Hardware arch
 GPC
 SM
 Core(SP)

devices
gtx1080ti
pascal arch
11G GDDR5x
11G bps
1582MHz
3584 cores (28 sm * 128 cores), 6 GPC
352bits
484GB/s
