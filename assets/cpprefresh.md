
c++-11

enum class

```
enum class Color {red, green, yellow};
Color x{Color::red};
Color x = red; //error, red not in scope
Color y = 1; //error, cannot convert int to color

```
enum class is strongly typed, its enumerators are scoped. plian enum doesn't have these features.
