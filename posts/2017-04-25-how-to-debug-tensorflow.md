---
layout: post
title: "How to debug tensorflow"
date: 2017-04-25
categories: howtos
commentIssueId: 2
---

Note that this is about debugging tesorflow itself, not about debugging programs written on tensorflow.

For python part, you can just use pdb:

```
import pdb
pdb.run('1+2')
pdb>>
```

For c/c++ part, you can do with the following 2 steps:

 1. build tensorflow with debug option  
   You need to add debug option when run ./configure:
    ```
    CC_OPT_FLAGS=-g ./configure
    ```
   or add --copt=-g after bazel build 
   
   ```
   bazel build -c opt --copt=-g  --config=cuda //tensorflow/cc:tutorials_example_trainer
   ```
   
   and then follow tensorflow [install from source steps](https://www.tensorflow.org/install/install_sources).  
   You will get a mush larger (~373M as of 1.1.0rc2) whl package.
 2. use gdb to start python   
    ```
    $ gdb python
    GNU gdb (GDB) Fedora 7.10.1-31.fc23
    Copyright (C) 2015 Free Software Foundation, Inc.
    License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
    This is free software: you are free to change and redistribute it.
    There is NO WARRANTY, to the extent permitted by law.  Type "show copying"
    and "show warranty" for details.
    This GDB was configured as "x86_64-redhat-linux-gnu".
    Type "show configuration" for configuration details.
    For bug reporting instructions, please see:
    <http://www.gnu.org/software/gdb/bugs/>.
    Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.
    For help, type "help".
    Type "apropos word" to search for commands related to "word"...
    Reading symbols from python...Reading symbols from /home/lie/python...(no debugging symbols found)...done.
    (no debugging symbols found)...done.
    Missing separate debuginfos, use: dnf debuginfo-install python-2.7.11-11.fc23.x86_64
    (gdb) r
    Starting program: /usr/bin/python
    [Thread debugging using libthread_db enabled]
    Using host libthread_db library "/lib64/libthread_db.so.1".
    Python 2.7.11 (default, Sep 29 2016, 13:33:00)
    [GCC 5.3.1 20160406 (Red Hat 5.3.1-6)] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import tensorflow as tf
    [New Thread 0x7fffeb9d6700 (LWP 4016)]
    [New Thread 0x7fffe91d5700 (LWP 4017)]
    [New Thread 0x7fffe89d4700 (LWP 4018)]
    [Thread 0x7fffe89d4700 (LWP 4018) exited]
    [Thread 0x7fffe91d5700 (LWP 4017) exited]
    [Thread 0x7fffeb9d6700 (LWP 4016) exited]
    Detaching after fork from child process 4071.
    >>>
    >>> a=tf.constant(1)
    >>> b=tf.constant(2)
    >>> c=a+b
    >>> sess=tf.Session()
    2017-04-26 23:17:20.882000: W tensorflow/core/platform/cpu_feature_guard.cc:45] The TensorFlow library wasn't compiled to use SSE4.1 instructions, but these are available on your machine and could speed up CPU computations.
    2017-04-26 23:17:20.882080: W tensorflow/core/platform/cpu_feature_guard.cc:45] The TensorFlow library wasn't compiled to use SSE4.2 instructions, but these are available on your machine and could speed up CPU computations.
    [New Thread 0x7fffe89d4700 (LWP 4092)]
    [New Thread 0x7fffe91d5700 (LWP 4093)]
    [New Thread 0x7fffeb9d6700 (LWP 4094)]
    [New Thread 0x7fffd59ff700 (LWP 4095)]
    [New Thread 0x7fffd51fe700 (LWP 4096)]
    [New Thread 0x7fffd49fd700 (LWP 4097)]
    [New Thread 0x7fffbffff700 (LWP 4098)]
    [New Thread 0x7fffbf7fe700 (LWP 4099)]
    >>>
    Program received signal SIGINT, Interrupt.
    0x00007ffff6e1d903 in select () from /lib64/libc.so.6
    (gdb) b TF_ExtendGraph
    Breakpoint 1 at 0x7fffdd653a90: file tensorflow/c/c_api.cc, line 351.
    (gdb) c
    Continuing.
    sess.run(c)

    Breakpoint 1, TF_ExtendGraph (s=s@entry=0x5555561a5f30, proto=proto@entry=0x7fffd5d8b10c, proto_len=proto_len@entry=141, status=status@entry=0x5555570f3060)
        at tensorflow/c/c_api.cc:351
    351	                    size_t proto_len, TF_Status* status) {
    (gdb) l
    346	  delete s->session;
    347	  delete s;
    348	}
    349
    350	void TF_ExtendGraph(TF_DeprecatedSession* s, const void* proto,
    351	                    size_t proto_len, TF_Status* status) {
    352	  GraphDef g;
    353	  if (!tensorflow::ParseProtoUnlimited(&g, proto, proto_len)) {
    354	    status->status = InvalidArgument("Invalid GraphDef");
    355	    return;
    (gdb) info args
    s = 0x5555561a5f30
    proto = 0x7fffd5d8b10c
    proto_len = 141
    status = 0x5555570f3060
    (gdb) bt
    #0  TF_ExtendGraph (s=s@entry=0x5555561a5f30, proto=proto@entry=0x7fffd5d8b10c, proto_len=proto_len@entry=141, status=status@entry=0x5555570f3060)
        at tensorflow/c/c_api.cc:351
    #1  0x00007fffdd4914f7 in _wrap_TF_ExtendGraph (args=<optimized out>) at bazel-out/local-opt/bin/tensorflow/python/pywrap_tensorflow_internal.cc:5805
    #2  0x00007ffff7af2796 in PyEval_EvalFrameEx () from /lib64/libpython2.7.so.1.0
    #3  0x00007ffff7af5624 in PyEval_EvalCodeEx () from /lib64/libpython2.7.so.1.0
    #4  0x00007ffff7af22ae in PyEval_EvalFrameEx () from /lib64/libpython2.7.so.1.0
    #5  0x00007ffff7af5624 in PyEval_EvalCodeEx () from /lib64/libpython2.7.so.1.0
    #6  0x00007ffff7a7df8c in function_call () from /lib64/libpython2.7.so.1.0
    #7  0x00007ffff7a59473 in PyObject_Call () from /lib64/libpython2.7.so.1.0
    #8  0x00007ffff7aed41b in PyEval_EvalFrameEx () from /lib64/libpython2.7.so.1.0
    #9  0x00007ffff7af5624 in PyEval_EvalCodeEx () from /lib64/libpython2.7.so.1.0
    #10 0x00007ffff7af22ae in PyEval_EvalFrameEx () from /lib64/libpython2.7.so.1.0
    #11 0x00007ffff7af5624 in PyEval_EvalCodeEx () from /lib64/libpython2.7.so.1.0
    #12 0x00007ffff7af22ae in PyEval_EvalFrameEx () from /lib64/libpython2.7.so.1.0
    #13 0x00007ffff7af5624 in PyEval_EvalCodeEx () from /lib64/libpython2.7.so.1.0
    #14 0x00007ffff7af22ae in PyEval_EvalFrameEx () from /lib64/libpython2.7.so.1.0
    #15 0x00007ffff7af5624 in PyEval_EvalCodeEx () from /lib64/libpython2.7.so.1.0
    #16 0x00007ffff7af22ae in PyEval_EvalFrameEx () from /lib64/libpython2.7.so.1.0
    #17 0x00007ffff7af5624 in PyEval_EvalCodeEx () from /lib64/libpython2.7.so.1.0
    #18 0x00007ffff7af5749 in PyEval_EvalCode () from /lib64/libpython2.7.so.1.0
    #19 0x00007ffff7b0ef8f in run_mod () from /lib64/libpython2.7.so.1.0
    #20 0x00007ffff7b10fea in PyRun_InteractiveOneFlags () from /lib64/libpython2.7.so.1.0
    #21 0x00007ffff7b111ce in PyRun_InteractiveLoopFlags () from /lib64/libpython2.7.so.1.0
    #22 0x00007ffff7b1185e in PyRun_AnyFileExFlags () from /lib64/libpython2.7.so.1.0
    #23 0x00007ffff7b234b1 in Py_Main () from /lib64/libpython2.7.so.1.0
    #24 0x00007ffff6d45580 in __libc_start_main () from /lib64/libc.so.6
    #25 0x0000555555554839 in _start ()
    ```
