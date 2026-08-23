// Deliberate trap: same function name `normalize` in an unrelated scope.
// legacy::normalize has nothing to do with geom::VectorMath::normalize.
namespace legacy {

float normalize(float raw) {
    return raw * 0.5f;
}

}  // namespace legacy