// Unicode position trap: emoji 🚀, non-BMP astral 𝔘𝔫𝔦𝔠𝔬𝔡𝔢, and accented
// characters café перед the queried symbol are on the same line, so UTF-16
// columns must be computed correctly.
export function measureCafé(record: string): number {
    return record.length;
}