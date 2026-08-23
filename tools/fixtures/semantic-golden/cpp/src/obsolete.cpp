// Dead symbol trap: obsolete_helper is defined but never called anywhere.
namespace legacy {
float obsolete_helper(float value) {
    return value + 1.0f;
}
}  // namespace legacy