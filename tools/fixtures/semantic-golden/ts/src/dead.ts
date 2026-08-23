// Dead symbol trap: exported but never imported or referenced anywhere.
export function orphanHelper(value: string): string {
    return value.trim();
}