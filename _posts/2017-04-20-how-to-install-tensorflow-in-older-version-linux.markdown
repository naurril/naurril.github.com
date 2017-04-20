---
layout: post
title: "How to install tensorflow in old version linux"
date: 2017-04-20
categories: howtos
---
Prebuilt Tensorflow(1.0.1) uses libc runtime v2.17 or above, if you install it on earlier linux version, like ubuntu 12.04, you will get the following err message when importing tensorflow in python(2.7):
```
ImportError: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.17' not found (required by /usr/local/lib/python2.7/dist-packages/tensorflow/python/_pywrap_tensorflow.so)
```

There are several methods to solve it but the most convenient one I found is to zip a new runtime library in other new version linux system, unzip them in some local folder, and then start python with the following command:
```
LD_LIBRARY_PATH=/path/to/your/unzipped/lib /path/to/your/unzipped/lib/ld-x.xx.so /path/to/your/python/bin/python
```

Incase you don't have a newer linux box, here is a [zipped libc] for x86-64 platform, I tried it on centos(kernel version 2.6.37) and it worked.


[zipped libc]: /assets/myglibc.tar.gz
