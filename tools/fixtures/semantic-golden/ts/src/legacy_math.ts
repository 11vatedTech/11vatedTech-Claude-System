// Same function name as duplicated.ts, different semantics: returns the
// count, not the weighted sum. Distinct symbol; must never be conflated.
export function computeScore(items: number[]): number {
    return items.length;
}