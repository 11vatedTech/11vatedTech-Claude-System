#include "vector_math.h"

namespace geom {

float VectorMath::normalize(float value, float min_value, float max_value) {
    if (max_value <= min_value) {
        return 0.0f;
    }
    return (value - min_value) / (max_value - min_value);
}

float VectorMath::clamp01(float value) {
    return value < 0.0f ? 0.0f : (value > 1.0f ? 1.0f : value);
}

}  // namespace geom