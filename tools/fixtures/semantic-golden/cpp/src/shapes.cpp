#include "shape.h"

namespace geom {

Circle::Circle(float radius) : radius_(radius) {}
Square::Square(float side) : side_(side) {}

float Circle::area() const { return 3.14159f * radius_ * radius_; }
float Square::area() const { return side_ * side_; }

// Direct concrete call: static and dynamic target both Circle::area.
float DirectConcreteArea() {
    Circle circle(2.0f);
    return circle.area();
}

// Base-pointer virtual call: static symbol Shape::area, possible overrides
// Circle::area and Square::area; the runtime target cannot be proven statically.
float DispatchThroughBase(Shape* shape) {
    return shape->area();
}

}  // namespace geom