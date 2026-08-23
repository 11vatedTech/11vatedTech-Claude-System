#pragma once
namespace geom {

class VectorMath {
public:
    // Declaration only; implementation lives in the .cpp.
    static float normalize(float value, float min_value, float max_value);
    static float clamp01(float value);
};

}  // namespace geom