#pragma once
namespace geom {

class Shape {
public:
    virtual ~Shape() = default;
    virtual float area() const = 0;  // virtual: static dispatch is impossible
};

class Circle : public Shape {
public:
    explicit Circle(float radius);
    float area() const override;
private:
    float radius_;
};

class Square : public Shape {
public:
    explicit Square(float side);
    float area() const override;
private:
    float side_;
};

}  // namespace geom