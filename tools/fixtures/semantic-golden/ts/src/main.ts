import { Engine, type Launcher } from "./launcher";
import { FlyLauncher } from "./fly_launcher";
import { createDefaultLauncher } from "./factory";

// Direct call through the concrete class: static receiver type is Engine.
const engine = new Engine();
export const direct = engine.launch("alpha");

// Indirect call through an interface. At this call site the static receiver
// type is Launcher, NOT FlyLauncher. The type-resolved call graph must report
//   STATIC_CALL_EDGE:      Launcher.launch
//   POSSIBLE_DISPATCH_EDGE: FlyLauncher.launch, RocketLauncher.launch
//   FLOW_INFERRED_EDGE:     FlyLauncher.launch (from `new FlyLauncher()`),
//                           certainty LIKELY, never PROVEN from interface
//                           semantics alone.
const launcher: Launcher = new FlyLauncher();
export const indirect = launcher.launch("beta");

// Interface reference where the concrete implementation is NOT locally
// obvious: the factory returns Launcher; static analysis cannot prove which
// implementation runs.
const fromFactory: Launcher = createDefaultLauncher();
export const factoryResult = fromFactory.launch("gamma");

// Deliberate trap: dynamic property access. obj[methodName]() is not a
// statically resolvable concrete call; the semantic system must not overclaim.
const dict: Record<string, (s: string) => string> = {
    launch: (s) => `dict:${s}`,
};
export function dynamicDispatch(key: string): string {
    const fn = dict[key];
    if (fn) {
        return fn("delta");
    }
    return "none";
}