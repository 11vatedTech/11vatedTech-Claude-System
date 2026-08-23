namespace geom {

// Overload trap (class J): two functions share the name `draw`.
int draw(int value) { return value; }
float draw(float value) { return value + 0.5f; }

}  // namespace geom