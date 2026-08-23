import type { Launcher } from "./launcher";
import { FlyLauncher } from "./fly_launcher";

// Returns the interface type; the concrete implementation is deliberately
// hidden inside this factory so callers cannot prove it statically.
export function createDefaultLauncher(): Launcher {
    return new FlyLauncher();
}