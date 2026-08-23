namespace geom {

// Template symbol: instantiations are generated symbols, not hand-written.
template <typename T>
T clamp(T value, T lo, T hi) {
    return value < lo ? lo : (value > hi ? hi : value);
}

// Documentation-only claim (class F): future_deadline_api is mentioned in this
// comment but never declared. Lexical search would find the token here.
// See ADR-4 for the planned future_deadline_api() contract.

}  // namespace geom