// Generic interface (class I): implementations parameterize T differently.
export interface Container<T> {
    put(item: T): void;
    get(): T | undefined;
}

export class Box<T> implements Container<T> {
    private items: T[] = [];
    put(item: T): void {
        this.items.push(item);
    }
    get(): T | undefined {
        return this.items.pop();
    }
}

export class StringBag implements Container<string> {
    private items: string[] = [];
    put(item: string): void {
        this.items.unshift(item);
    }
    get(): string | undefined {
        return this.items.shift();
    }
}