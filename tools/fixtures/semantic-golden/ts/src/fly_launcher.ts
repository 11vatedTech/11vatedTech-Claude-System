import type { Launcher } from "./launcher";

export class FlyLauncher implements Launcher {
    launch(name: string): string {
        return `fly:${name}`;
    }
}