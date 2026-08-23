// Callback trap (class K): onComplete is passed as a plain function value.
// There is no direct call site naming ReportSink; the edge exists only
// through the function-type parameter.
export interface ReportSink {
    (line: string): void;
}

export function renderReport(onComplete: ReportSink, lines: string[]): void {
    for (const line of lines) {
        onComplete(line);
    }
}

export function writeLog(line: string): void {
    console.log(line);
}

// The call edge renderReport -> writeLog only becomes visible through the
// function-type binding below.
export function emit(lines: string[]): void {
    renderReport(writeLog, lines);
}