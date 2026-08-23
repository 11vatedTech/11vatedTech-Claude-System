export interface Launcher {
    launch(name: string): string;
}

export class Engine {
    launch(name: string): string {
        return `engine:${name}`;
    }
}