// Function overloads: two signatures share the name `adjust`. Implementations
// and call sites are distinct symbols at the type level, but both share the
// same declaration name (trap class J).
export function adjust(value: string): number;
export function adjust(value: number): string;
export function adjust(value: string | number): string | number {
    return typeof value === "string" ? value.length : `n${value}`;
}