---
layout: post
title: "SBCL multi-thread debug method"
date: 2015-07-11
categories: howtos
commentIssueId: 1
---




SBCL manual中对多线程的debug其实有说明，线程有3个状态：foreground、background、stopped。当background线程出现了异常停止运行时，一般会打印错误信息，但是没有位置信息和调用栈，无法直接分析。此时在forground线程中调用(sb-thread:release-foreground)即可将后台停止的线程变成前台线程，可以正常使用各种调试命令。



例子：

* (sb-thread:make-thread (lambda () (funcall 'foo-func 0)))
#<#<SB-THREAD:THREAD RUNNING {245E39F1}>

debugger invoked on a UNDEFINED-FUNCTION in thread
* #<THREAD RUNNING {245E39F1}>:
  The function COMMON-LISP-USER::FOO-FUNC is undefined.

(+ 1 2) 
3
* (sb-thread:release-foreground)


