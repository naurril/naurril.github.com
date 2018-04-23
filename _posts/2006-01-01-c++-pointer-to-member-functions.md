---
layout: post
title: "C++ 成员函数指针揭秘"
date: 2006-01-01
categories: howtos
commentIssueId: 1
---



[TOC]

# 前言


C++语言支持指向成员函数的指针这一语言机制。就像许多其它C++语言机制一样，它也是一把双刃剑，用得好，能够提高程序的灵活性、可扩展性等等，但是也存在一些不易发现的陷阱，我们在使用它的时候需要格外注意, 尤其是在我们把它和c++其它的语言机制合起来使用的时候更是要倍加当心。

**关键字**：成员函数指针，继承，虚函数，this指针调整，static_cast

2018.4 注：此文多年前写成，有些细节可能已经发生了变化，但是对理解c++对象模型和实现仍然有参考价值。

# 语法

C++成员函数指针（pointer to member function）的用法和C语言的函数指针有些相似.

下面的代码说明了成员函数指针的一般用法：
```c++
class ClassName {public: int foo(int); }

int (ClassName::*pmf)(int) = &ClassNmae::foo;

ClassName  c;   //.*的用法，经由对象调用
(c.*pmf)(5);      // A

ClassName *pc = &c;  //->*的用法，经由对象指针调用
(Pc->*pmf)(6);   // B
```

使用typedef可以让代码变得略微好看一点：
```
typedef int （ClassName::*PMF）(int);
PMF pmf = &ClassName::foo;
```
注意获取一个成员函数指针的语法要求很严格： 
1. 不能使用括号：例如```&(ClassName::foo)```不对。
1. 必须有限定符：例如```&foo```不对。即使在类ClassName的作用域内也不行。
1. 必须使用取地址符号：例如直接写```ClassName::foo```不行。（虽然普通函数指针可以这样）
所以，必须要这样写：```&ClassName::foo```。

C++成员函数的调用需要至少3个要素：this指针，函数参数(也许为空)，函数地址。上面的调用中，->*和.*运算符之前的对象/指针提供了this（和真正使用this并不完全一致，后面会讨论），参数在括号内提供，pmf则提供了函数地址。

注意这里成员函数指针已经开始显示它“异类”的天性了。上面代码中注释A和B处两个表达式，产生了一个在C++里面没有类型(type)的“东西”（这是C++语言里面唯一的例外，其它任何东西都是有类型的），这就是.*和->*运算符：
```
(c.*pmf)
(Pc->*pmf)
```
这两个运算符求值生成的“东西”我们只知道可以把它拿来当函数调用一样使唤，别的什么也不能干，甚至都不能把它存在某个地方。就因为这个原因，Andrei Alexandrescu 在他那本著名的《Modern c++ design》里面就说，成员函数指针和这两个操作符号是“curiously half-baked concept in c++”。（5.9节）

C++里面引入了“引用”(reference)的概念，可是却不存在“成员函数的引用”，这也是一个特殊的地方。(当然，我们可以使用“成员函数指针”的引用，呵呵)

#与其它语言机制的混合使用

C++是一种Multi-Paradigm的语言，各种语言机制混合使用也是平常的事。这里我们只提几种会影响到成员函数指针实现和运行的语言机制。

## 继承
根据C++语言规定，成员函数指针具有contravariance特性，就是说，基类的成员函数指针可以赋值给继承类的成员函数指针，C++语言提供了默认的转换方式，但是反过来不行。

## 虚函数
首先要说明，指向虚拟成员函数（virtual function member）的指针也能正确表现出虚拟函数的特性。举例说明如下：
```c++
class B { 
  public virtual int foo(int) {
    /* B's implementation */
    return 0; 
  } 
};
class D : public B 
{ 
   public virtual int foo(int) {
      /* D's implementation */ 
      return 0; 
   } 
};

int foo(){
  int (B::*pmf)(int) = &B::foo;
  D d;
  B* pb = &d;
  (d.*pmf)(0);     //这里执行D::foo
  (pb->*pmf)(0);   //这里执行D::foo，多态
}
```
C++借由虚函数提供了运行时多态特性，虚函数的实现和普通函数有很大的不同。一般编译器都是采用大家都熟悉的v-table (virtual function table)的方式。所有的虚函数地址存在一个函数表里面，类对象中存储该函数表的首地址（vptr_point）。运行时根据this指针、虚函数索引和虚函数表指针找到函数调用地址。

![vptr_point](../../../../assets/vptr_point.png)

因为这些不同，所以成员函数指针碰上虚函数的时候，也需要作特殊的处理，才能正确表现出所期望的虚拟性质。
## 多继承
这里扯上多继承，是因为多继承的存在导致了成员函数指针的实现的复杂性。这是因为编译器有时候需要进行”this”指针调整。
举例说明如下：
class B1{};
class B2{};
class D: public B1, public B2{}
假设上面三个对象都不涉及到虚函数，D在内存中的典型布局如下图所示（如果有虚函数则多一个vptr指针， 差别不大）：

![vptr_multi_obj](../../../../assets/vptr_multi_obj.png)

现在假设我们经由D对象调用B2的函数，
D d；
d.fun_of_b2();  

这里传给fun_of_b2的this指针不能是&d, 而应该对&d加上一个偏移，得到D内含的B2子对象的首地址处。

成员函数指针的实现必须考虑这种情况。

多继承总是不那么受欢迎。不过即使是单继承，上面的情况也会出现。考虑下面的例子:
class B{};  //non-virtual class
class D :public B{}; //virtual class

假设B是一个普通的类，没有虚拟成员函数。而D加上了虚拟成员函数。那么D的典型内存布局如下图所示：

![vptr_multi_obj2](../../../../assets/vptr_multi_obj2.png)

因为D引入了vptr指针，而一般的实现都将vptr放在对象的开头，这就导致经由D对象访问B的成员函数的时候，仍然需要进行this指针的调整。
D d；
d.fun_of_b();  //this 指针也需要调整，否则fun_of_b的行为就会异常

# 实现


从上面一节我们可以看到，编译器要实现成员函数指针，有几个问题是绕不过去的：
1）函数是不是虚拟函数，这个涉及到虚函数表(__vtbl)的访问。
2）函数运行时，需不需要调整this指针，如何调整。这个涉及到C++对象的内存布局。

事实上，成员函数指针必须记住这两个信息。为什么要记住是否为虚函数就不用解释了。但是this指针调整为什么要记住呢？因为在.*和->*运算符求值时必须用到。 考虑上面那个多继承的例子：
```c++
int (D::*pmf)(int) = &B2::foo_of_b2;  //A
D d;                           
(d.*pmf)(0);                      //B
```
看看上面的代码，其实我们在A处知道需要进行this指针调整，也知道该怎么调整。但是这时候this还没出世呢，还不到调整的时候。到了B处终于有了This指针了，可是又不知道该怎样调整了。所以pmf必须记住调整方式，到了B处调用的时候，再来进行调整。
## Microsoft的实现
### 内部表示
Microsoft VC的实现采用的是Microsoft一贯使用的Thunk技术（不知道这个名字怎么来的，不过有趣的是把它反过来拼写就变成了大牛Knuth的名字，呵呵）。

对于Mircosoft来说，成员函数指针实际上分两种，一种需要调节this指针，一种不需要调节this指针。
先分清楚那些情况下成员函数指针需要调整this指针，那些情况下不需要。回忆上一节讨论的c++对象内存布局的说明，我们可以得出结论如下：
如果一个类对象obj含有一些子对象subobj，这些子对象的首地址&subobj和对象自己的首地址&obj不等的话，就有可能需要调整this指针。因为我们有可能把subobj的函数当成obj自己的函数来使用。
根据这个原则，可以知道下列情况不需要调整this指针：
1. 继承树最顶层的类。
1. 单继承，若所有类都不含有虚拟函数，那么该继承树上所有类都不需要调整this指针。
1. 单继承，若最顶层的类含有虚函数，那么该继承树上所有类都不需要调整this指针。

下列情况可能进行this指针调整：
1. 多继承
1. 单继承，最顶的base class不含virtual function，但继承类含虚函数。那么这些继承类可能需要进行this指针调整。

Microsoft把这两种情况分得很清楚。所以成员函数的内部表示大致分下面两种：
```c++
struct pmf_type1{
	void* vcall_addr;
};

struct pmf_type2{
	void* vcall_addr;
	int  delta;  //调整this指针用
};
```
这两种表示导致成员函数指针的大小可能不一样，pmf_type1大小为4，pmf_type2大小为8。有兴趣的话可以写一段代码测试一下。

### Vcall_addr实现
上面两个结构中出现了vcall_addr, 它就是Microsoft 的Thunk技术核心所在。简单的说，vcall_addr是一个指针，这个指针隐藏了它所指的函数是虚拟函数还是普通函数的区别。事实上，若它所指的成员函数是一个普通成员函数，那么这个地址也就是这个成员函数的函数地址。若是虚拟成员函数，那么这个指针指向一小段代码，这段代码会根据this指针和虚函数索引值寻找出真正的函数地址，然后跳转(注意是跳转jmp，而不是函数调用call)到真实的函数地址处执行。
看一个例子。
```c++
//源代码
class  C
{
public:
	int nv_fun1(int) {return 0;}
	virtual int v_fun(int) {return 0;}
	virtual int v_fun_2(int) {return 0;}
};

void foo(C *c)
{
	int (C::*pmf)(int);

	pmf = &C::nv_fun1;
	(c->*pmf)(0x12345678);

	pmf = &C::v_fun;
	(c->*pmf)(0x87654321);

	pmf = &C::v_fun_2;
	(c->*pmf)(0x87654321);
}
```

```
; foo的汇编代码，release版本，部分地方进行了优化
:00401000 56                      push esi
:00401001 8B742408                mov esi, dword ptr [esp+08]
;	pmf = &C::nv_fun1;
;	(c->*pmf)(0x12345678);
:00401005 6878563412              push 12345678
:0040100A 8BCE                    mov ecx, esi ;this
:0040100C E81F000000              call 00401030
;	pmf = &C::v_fun;
;	(c->*pmf)(0x87654321);
:00401011 6821436587              push 87654321
:00401016 8BCE                    mov ecx, esi  ;this
:00401018 E803070000              call 00401720
;	pmf = &C::v_fun_2;
;	(c->*pmf)(0x87654321);
:0040101D 6821436587              push 87654321
:00401022 8BCE                    mov ecx, esi  ;this
:00401024 E807070000              call 00401730
:00401029 5E                      pop esi
:0040102A C3                      ret
:00401030 33C0    ; 函数实现       xor eax, eax    
:00401032 C20400                  ret 0004
:00401720 8B01    ; vcall           mov eax, dword ptr [ecx]
:00401722 FF20                    jmp dword ptr [eax]
:00401730 8B01    ; vcall          mov eax, dword ptr [ecx]
:00401732 FF6004                  jmp [eax+04]
```
![ass_foo](../../../../assets/ass_foo.png)

从上面的汇编代码可以看出vcall_addr的用法。00401030, 00401720, 00401730都是vcall_addr的值，其实也就是pmf的值。在调用的地方，我们不能分别出是不是虚函数，所看到的都是一个函数地址。但是在vcall_addr被当成函数地址调用后，进入vcall_addr，就有区别了。00401720, 00401730是两个虚函数的vcall，他们都是先根据this指针，计算出函数地址，然后jmp到真正的函数地址。00401030是C::nv_fun1的真实地址。

Microsoft的这种实现需要对一个类的每个用到了的虚函数，都分别产生这样的一段代码。这就像一个template函数:
```	
template <int index>
void vcall(void* this) 
{
jmp this->vptr[index]; //pseudo asm code
}
```
每种不同的index都要产生一个实例。

Microsoft就是采用这样的方式实现了虚成员函数指针的调用。
### This指针调整
不过还有一个this调整的问题，我们还没有解决。上面的例子为了简化，我们故意避开了this指针调整。不过有了上面的基础，我们再讨论this指针调整就容易了。
首先我们需要构造一个需要进行this指针调整的情况。回忆这节开头，我们讨论了哪些情况下需要进行this指针调整。我们用一个单继承的例子来进行说明。这次我们避开virtual/non-virtual function的问题暂不考虑。
```
class B { 
public: 
	B():m_b(0x13572468){}
	int b_fun(int) 	{
		std::cout<<'B'<<std::endl; 
		return 0; 
	} 
private:
	int m_b;
};

class D : public B { 
public: 
	D():m_d(0x24681357){}
	virtual int foo(int) 	{
		std::cout<<'D'<<std::endl;  
		return 0; 
	} 
private:
	int m_d;
};	// 注意这个例子中virtual的使用

void test_this_adjust(D *pd, int (D::*pmf)(int))
{
	(pd->*pmf)(0x12345678);
}
:00401000   mov eax, dword ptr [esp+04] ; this入参
:00401004   mov ecx, dword ptr [esp+0C] ; delta入参
:00401008   push 12345678 ；参数入栈
:0040100D   add ecx, eax ; this = ecx= this+delta
:0040100F   call [esp+0C] ; vcall_addr入参
:00401013   ret


void test_main(D *pd)
{
	test_this_adjust(pd, &D::foo);
	test_this_adjust(pd, &B::b_fun);
}
; test_this_adjust(pd, &D::foo);
:00401020  xor ecx, ecx
:00401022  push esi
:00401023  mov esi, dword ptr [esp+08] ; pd, this指针
:00401027  mov eax, 004016A0 ; D::foo vcall地址
:0040102C  push ecx ; push delat = 0, ecx=0
:0040102D  push eax ; push vcall_addr
:0040102E  push esi  ; push this
:0040102F  call 00401000 ; call test_this_adjust

; test_this_adjust(pd, &B::b_fun);
:00401034  mov ecx, 00000004 ;和上面的调用不同了
:00401039  mov eax, 00401050 ; B::b_fun地址
:0040103E  push ecx ; push delta = 4, exc=4
:0040103F  push eax ; push vcall_addr, B::b_fun地址
:00401040  push esi ; push this
:00401041  call 00401000  ; call test_this_adjust

:00401046  add esp, 00000018
:00401049  pop esi
:0040104A  ret
```
注意这里和上面一个例子的区别：

在调用```test_this_adjust(pd, &D::foo)```的时候，实际上传入了3个参数，调用相当于
```
test_this_adjust(pd, vcall_address_of_foo, delta(=0));
```

调用```test_this_adjust(pd, &B::b_fun)```的时候，也是3个参数
```
test_this_adjust(pd, vcall_address_of_b_fun, delta(=4));
```

两个调用有个明显的不同，就是delta的值。这个delta，为我们后来调整this指针提供了帮助。

再看看test_this_adjust函数的汇编代码，和上一个例子的不同，也就是多了一句代码：
```
:0040100D   add ecx, eax ; this = ecx= this+delta
```
这就是对this指针作必要的调整。
### 结论

Microsoft根据情况选用下面的结构表示成员函数指针，使用Thunk技术（vcall_addr）实现虚拟函数/非虚拟函数的自适应，在必要的时候进行this指针调整(使用delta)。

```c++
struct pmf_type1{
	void* vcall_addr;
};

struct pmf_type2{
	void* vcall_addr;
	int  delta;  //调整this指针用
};
```

## GCC的实现

GCC对于成员函数指针的实现和Microsoft的方式有很大的不同。

### 内部表示

GCC对于成员函数指针统一使用类似下面的结构进行表示：

```c++
struct
{
	void* __pfn;  //函数地址，或者是虚拟函数的index
	long __delta;	// offset, 用来进行this指针调整
};
```

### 实现机制

先来看看GCC是如何区分普通成员函数和虚拟成员函数的。

不管是普通成员函数，还是虚拟成员函数，信息都记录在__pfn里面。这里有个小小的技巧。我们知道一般来说因为对齐的关系，函数地址都至少是4字节对齐的。这就意味这一个函数的地址，最低位两个bit总是0。（就算没有这个对齐限制，编译器也可以这样实现。） GCC充分利用了这两个bit。如果是普通的函数，__pfn记录该函数的真实地址，最低位两个bit就是全0，如果是虚拟成员函数，最后两个bit不是0，剩下的30bit就是虚拟成员函数在函数表中的索引值。

使用的时候，GCC先取出最低位两个bit看看是不是0，若是0就拿这个地址直接进行函数调用。若不是0，就取出前面30位包含的虚拟函数索引，通过计算得到真正的函数地址，再进行函数调用。

GCC和Microsoft对这个问题最大的不同就是GCC总是动态计算出函数地址，而且每次调用都要判断是否为虚拟函数，开销自然要比Microsoft的实现要大一些。这也差不多可以算成一种时间换空间的做法。

在this指针调整方面，GCC和Mircrosoft的做法是一样的。不过GCC在任何情况下都会带上__delta这个变量，如果不需要调整，__delta＝0。

这样GCC的实现比起Microsoft来说要稍简单一些。在所有场合其实现方式都是一样的。而且这样的实现也带来多一些灵活性。这一点下面“陷阱”一节再进行说明。

GCC在不同的平台其实现细节可能略有不同，我们来看一个基于Intel平台的典型实现：

```c++
//source code
int test_fun(Base *pb, int (Base::*pmf)(int))
{
	return (pb->*pmf)(4);
}
```
```
//assembly
8048478:	push   %ebp
 8048479:	mov    %esp,%ebp
 804847b:	sub    $0x18,%esp
 804847e:	mov    0xc(%ebp),%eax   ;__pfn， 入参
 8048481:	mov    0x10(%ebp),%edx  ;__delta， 入参
 8048484:	mov    %eax,0xfffffff8(%ebp)  ; __pfn
 8048487:	mov    %edx,0xfffffffc(%ebp)  ; __delta
 804848a:	sub    $0x8,%esp	     ; 
 804848d:	mov    0xfffffff8(%ebp),%eax ; __pfn
 8048490:	and    $0x1,%eax             ; __test last 2 bits, 判断是否为虚拟函数
 8048493:	test   %al,%al
 8048495:	je     80484b6 <_Z8test_funP4BaseMS_FiiE+0x3e> ；不是虚函数就跳到 non-virtual fun处

  ; virtual fun，是虚拟函数，计算函数地址
 8048497:	mov    0xfffffffc(%ebp),%eax ;__delta 
 804849a:	mov    0x8(%ebp),%ecx  ;get pb， 入参
 804849d:	add    %eax,%ecx       ;ecx = this=pb+__delta
 804849f:	mov    0xfffffff8(%ebp),%eax ;eax=__pfn
 80484a2:	shr    $0x2,%eax             ;eax=__pfn>>2 (fun index)
 80484a5:	lea    0x0(,%eax,4),%edx     ;edx=eax * 4
 80484ac:	mov    (%ecx),%eax	         ;eax=vtble
 80484ae:	mov    (%eax,%edx,1),%edx    ;edx为函数地址
 80484b1:	mov    %edx,0xfffffff4(%ebp)   ;存起来
 80484b4:	jmp    80484bc <_Z8test_funP4BaseMS_FiiE+0x44>

 ; non-virtual fun，不是虚拟函数，直接取出函数地址
 80484b6:	mov    0xfffffff8(%ebp),%eax ;__pfn, fun addr
 80484b9:	mov    %eax,0xfffffff4(%ebp) ;__pfn, fun addr

                ; common invoking
                ; 0xfffffff4(%ebp) contains fun address
 80484bc:	push   $0x4                 ;push parameters
 80484be:	mov    0xfffffffc(%ebp),%eax   ; delta
 80484c1:	add    0x8(%ebp),%eax        ; this ＝ pb＋delta, this指针调整
 80484c4:	push   %eax                  ; this
 80484c5:	call   *0xfffffff4(%ebp)     ;invoke
 80484c8:	add    $0x10,%esp
 80484cb:	leave  
 80484cc:	ret    
 80484cd:	nop      
```

# 语言限制与陷阱


按照C++语言的规定，对于成员函数指针的使用，有如下限制：

*不允许继承类的成员函数指针赋值给基类成员函数指针*。

如果我们一定要反其道而行，则存在this指针调整的陷阱，需要注意。这一节我们通过两个例子，说明为什么这样操作是危险的。

## 例子
先看一个单继承的例子。

```c++
class B { 
public: 
	B():m_b(0x13572468){}
    /* virtual */	int b_fun(int) {  //A
		std::cout<<'B'<<std::endl; 
		return 0; 
	} 
private:
	int m_b;
};
class D : public B { 
public: 
	D():m_d(0x24681357){}
	virtual int foo(int) {     // B
		std::cout<<'D'<<std::endl;  
		return 0; 
	} 
private:
	int m_d;
};
void test_consistent(B* pb, int (B::*pmf)(int))
{
	(pb->*pmf)(0x12345678);
}
void test_main(D *pd)
{
	typedef int (B::*B_PMF)(int);
	//test_consistent(pd, &D::foo);  error！
	test_consistent(pd, static_cast<B_PMF>(&D::foo));
     // crash in MSVC
}

int main()
{
	D d;
	test_main(&d);
	return 0;
}	
```

这句话在Microsoft Visual C++6.0下面一运行就crash。 表面上看我们传的指针是D的指针，函数也是D的函数。但实际上不是那么简单。函数调用的时候，pd赋值给pb，编译器会进行this指针调整，pb指向pd内部B的子对象。这样到了test_consistent函数内部的时候，就是用D::B对象调用D::foo函数，this指针不对，所以就crash了。

上面这个问题，GCC能正确的进行处理。其实错误的原因不在于pb=pd指针赋值的时候，编译器将指针进行了调整，而在于在test_consistent内，成员函数指针被调用的时候，应该将this指针再调整回去！这个问题又是由static_cast的行为不适当引起的。
```c++
static_cast<B_PMF>(&D::foo) 
```
这里的static_cast, 是将D的成员函数指针强制转换为给B的成员函数指针。因为它是D的函数，虽然会经由B的指针或者对象调用，但是调用时this指针应该根据B的地址调整成D的首地址。所以经过static_cast之后，这个成员函数指针应该为{__pfn,  __delta= -4 }。（B被包含在D内部，所以这里是－4！） GCC正确的执行了这个cast，并且每次使用成员函数指针调用时都进行this指针调整， 所以没有问题。可是Microsoft的实现在这个地方却无能为力，为什么呢？就算static_cast正确，在test_consistent里面根本就不会进行this指针调整！ 因为它使用的其实是 struct{void *vcall_address;}这个结构，根本不知道要进行this指针调整。

Microsoft在这里要做的是将一个struct pmf_type2类型的对象，通过static_cast转换成一个struct pmf_type1的对象。这种转换根本不能成功，因为struct pmf_type1要少一个成员delta.这样的转换会丢失信息。
当然我们不能怪Microsoft，C++语言本来就规定了不能这样用。不过Microsoft可以做得更好一点，至少可以不允许这样的static_cast。（这样的用法, VC2005能够给出一个告警, 提示有可能产生不正确的代码!）
	
我们可以很简单的解决这个问题，在上面的代码中A处，把注释掉的virtual打开，也可以把B处的virtual注释掉，使得所有地方都无需进行this调整，问题也就不再出现了。

这个例子可能有些牵强，我们把上面的代码稍做修改，再举一个涉及到多继承的例子。
```c++
class B { 
public: 
	B():m_b(0x13572468){}
	virtual int b_fun(int) 	{
		std::cout<<"B "<<std::hex<<m_b<<std::endl; 
		return 0; 
	} 
private:
	int m_b;
};

class B2 {
public:
	B2():m_b2(0x24681357){}
	int b2_fun(int) 	{
		std::cout<<"B2 "<<std::hex<<m_b2<<std::endl; 
		return 0; 
	} 
private:
	int m_b2;
};

class D :public B , public B2
{ 
public: 
	D():m_d(0x24681357){}
	int foo(int) 
	{
		std::cout<<"D "<<std::hex<<m_d<<std::endl;  
		return 0; 
	} 
private:
	int m_d;
};

 
void test_consistent(B* pb, int (B::*pmf)(int))
{
	(pb->*pmf)(0x12345678);
}

void test_main(D *pd)
{
	typedef int (B::*B_PMF)(int);
	//test_consistent(pd, &B2::b2_fun);                    //A
	//test_consistent(pd, static_cast<B_PMF>(&B2::b2_fun));  // B
	typedef int (D::*D_PMF)(int);                        // C
	D_PMF pmf = &B2::b2_fun;               // D
	test_consistent(pd, static_cast<B_PMF>(pmf)); // E 结果错误！
}

int main()
{
	D d;
	test_main(&d);
	return 0;
}	
```

先用Microsoft Visual C++进行测试。这段代码执行结果是错误的。（没有crash，比crash更糟）。先看注释A处，语法错误，VC给出了正确的编译错误。

B处，进行static_cast, VC也能给出正确的编译错误，说int (B2::*)(int)类型不能转换成int (B::*)(int)类型。这也很好。

这样都不行，我们就绕一下，来个“智取”。先将int (B2::*)(int)转换为int (D::*)(int)。这个转换是C++标志规定必须实现的，属于基类成员函数指针赋值给继承类成员函数指针。然后再进一步使用static_cast转换成int (B::*)(int)类型。编译错误没有了。可是执行结果不正确！原因和上一个例子一样，this指针不能正确的进行调整。这里D类是需要进行this指针调整的，而B类，B2类都不需要调整，在test_consistent中调用函数指针的时候，不会进行this指针调整，所以出现了错误。

这个例子，GCC表现也相当好。这都归根于GCC采用一致的成员函数指针的表示和实现!

在Microsoft新发布的Visual C++2005中, 上面的问题仍然存在。(再重复一下, 这不怪Microsoft, C++标准本来就不允许这样用。)

## static_cast干了些什么

GCC里面，不同类型的成员函数指针使用static_cast进行转换，就是计算出合适的__delta值。
VC里面，使用static_cast进行转换，做了什么?

## 默认的转换

C++规定编译器必须提供一个从基类成员函数指针到继承类成员函数指针的默认转换。这个转换，最关键的地方，其实也是this指针调整。

## 教训

从上面的例子，我们得到如下教训：
1. static_cast不能随便用。
1. 一般情况下不要将继承类的成员函数指针赋值给基类成员函数指针。不同编译器可能有不同的表现。这可能导致潜在的可移植性问题。

## 如何避开陷阱
现在我们明白了将C++运行时多态特性和C++成员函数指针合起来使用的时候，可能有些不够自然的地方，而且存在上面所描述的陷阱。这些陷阱都是因为this指针调整引起的。所以要避开这个陷阱，就要避开this指针调整，所以需要注意：
1. 不要使用static_cast将继承类的成员函数指针赋值给基类成员函数指针，如果一定要使用，首先确定没有问题。（这条可能会限制代码的可扩展性。）
1. 如果一定要使用static_cast, 注意不要使用多继承。
1. 如果一定要使用多继承的话，不要把一个基类的成员函数指针赋值给另一个基类的函数指针。
1. 单继承要么全部不使用虚函数，要么全部使用虚函数。不要使用非虚基类，却让子类包含虚函数。

最后，用Herb Sutter的话结个尾（如果我没记错的话）：do what you know，and know what you do！




# 参考书目
1. Modern C++ design, Andrei Alexandrescu
1. Inside the C++ Object model, Stanley B. lippman
1. C++ Common Knowledge: Essential Intermediate Programming, Stephen C. Dewhurst
1. The C++ Programming Language (special edition), Bjarne Stroustrup,




