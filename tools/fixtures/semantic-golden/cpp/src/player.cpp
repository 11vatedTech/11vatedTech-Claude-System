#include "vector_math.h"

// The only real caller of VectorMath::normalize in the fixture.
float ComputePlayerHealth(float damage, float max_health) {
    const float ratio = geom::VectorMath::normalize(max_health - damage, 0.0f, max_health);
    return geom::VectorMath::clamp01(ratio);
}