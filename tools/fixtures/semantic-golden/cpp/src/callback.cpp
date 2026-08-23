#include <functional>

namespace geom {

// Callback trap (class K): run_after invokes its arg; the concrete callee is
// only visible through the binding, not at the call site.
void run_after(std::function<void(float)> fn, float value) {
    fn(value);
}

void apply_gain(float value) {}

void schedule_gain() {
    run_after(apply_gain, 1.5f);
}

// Function-pointer variant.
using FnPtr = float (*)(float);
float curve(float v) { return v * v; }
void use_curve(FnPtr fn, float x) { fn(x); }
void schedule_curve() { use_curve(curve, 2.0f); }

}  // namespace geom