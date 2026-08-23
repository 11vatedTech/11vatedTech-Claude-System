#include "generated_config.h"

// Depends on the generated constant; references must resolve through the
// generated header even though clangd has no engine-side knowledge of it.
int CurrentSchema() {
    return build::kGeneratedVersion;
}