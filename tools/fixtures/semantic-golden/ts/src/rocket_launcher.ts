import type { Launcher } from "./launcher";

export class RocketLauncher implements Launcher {
    launch(name: string): string {
        return `rocket:${name}`;
    }
}