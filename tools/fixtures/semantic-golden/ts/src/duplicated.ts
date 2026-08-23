// Duplicate-looking but semantically different code (trap): this module's
// computeScore sums weights; legacy_math.ts counts items. A naive
// deduplication by shape would be wrong.
export function computeScore(items: number[]): number {
    return items.reduce((sum, item) => sum + item, 0);
}