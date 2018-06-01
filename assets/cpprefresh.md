
# c++-11

 "I learned a fair bit writing this book" --Bjarne stroustrup, The c++ programming language 4th edition, 1.3.2


## enum class (2.3.3)

```c++
enum class Color {red, green, yellow};
enum class Light {red, yellow};
Color x{Color::red};
Color x = red; //error, red not in scope
Color y = 1; //error, cannot convert int to color
Light z = Color::red; //error, different class
```
enum class is strongly typed, its enumerators are scoped. plian enum doesn't have these features.


## universal initialization form based on {}-list (6.3.5)
```c++
double x{2.4};
```
this form should provide a universal form to initialize variables. 

there are many initilization forms in c++
```c++
X a1 {v};
X a2 = {v};
X a3 = v;
X a4(v);
```
only the first can be used in every context, it's recommended.

but if used with ```auto```, use = instead.
```c++
auto x{5}; // x has type initialized_list<int>
auto x = 5; // x is a int
```

class member initializer can also use {}
```c++
struct Udt{
  Udt(int a):a{a}
  {}
private:
  int a;
}
```
TBD.

## constexpr (2.2.3, 10.4)
constexpr means roughly to be evaluated at compile time.
```c++
constexpr int foo(int a, int b){
    //int c = a+b;
    //return c+1;  // error, constexpr func can have only return statement.
    return a+b+1; // ok
}

int a[foo(2,10)]; 

```
constexpr functions can be used with variables as input arguments, as long as the returned value is not used in constexpr, you don't have to write two version of the same function, one for constexpr, one for variables.

## range-for-statement (2.2.5)
```c++
int a= {1,2,3,4,5}
for (auto x: a){
  foo(x)
}
```
you don't use index to traverse an array, eliminated out-of-bounds errors in this scenario.

## nullptr (7.2.2, 2.2)
using nullptr instead of 0 or NULL removes confusions between integers and pointers.

## static assertion
```c++
static_assert(sizeof(int) >4, "not ok in 32bit system")
```
check something in compile time, constexpr canbe used here.





