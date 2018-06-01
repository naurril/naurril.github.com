
c++-11

 "I learned a fair bit writing this book" --Bjarne stroustrup, The c++ programming language 4th edition, 1.3.2


enum class (2.3.3)

```c++
enum class Color {red, green, yellow};
enum class Light {red, yellow};
Color x{Color::red};
Color x = red; //error, red not in scope
Color y = 1; //error, cannot convert int to color
Light z = Color::red; //error, different class
```
enum class is strongly typed, its enumerators are scoped. plian enum doesn't have these features.


universal initialization form based on {}-list
```c++
double x{2.4};
```
this form should provide a universal form to initialize variables. 

there are many initilization form in c++
```c++
X a1 {v};
X a2 = {v};
X a3 = v;
X a4(v);
```
only the first can be used in every context, it's recommended.

but if it's used with auto, use = instead.
```c++
auto x{5}; // x has type initialized_list<int>
auto x = 5; // x is a int
```
TBD.
