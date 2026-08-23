// Deliberate trap: a module-local `launch` with no relation to Launcher.
function launch(prefix: string): string {
    return `local:${prefix}`;
}

export const local = launch("gamma");