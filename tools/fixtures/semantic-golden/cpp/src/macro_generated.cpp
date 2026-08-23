namespace geom {

// Macro-generated declaration (class E adjacency): the preprocessor expands
// DECLARE_GETTER into real functions. clangd sees the expanded declarations,
// but a plain text/lexical scan sees only the macro line.
#define DECLARE_GETTER(NAME) \
    float get_##NAME() const; \
    void set_##NAME(float v);

class Metrics {
public:
    DECLARE_GETTER(speed)
    DECLARE_GETTER(accel)
};

float Metrics::get_speed() const { return 0.0f; }
float Metrics::get_accel() const { return 0.0f; }

}  // namespace geom