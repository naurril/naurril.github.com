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
    (gdb) r    
    >>> import tensorflow as tf    
    >>> a=tf.constant(1)    
    >>> b=tf.constant(2)    
    >>> c=a+b    
    >>> sess=tf.Session()    
    >>> (Ctrl+C)    
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
    ```
