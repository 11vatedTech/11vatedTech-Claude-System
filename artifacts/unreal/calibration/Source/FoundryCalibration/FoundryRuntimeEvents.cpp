#include "FoundryRuntimeEvents.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

int32 UFoundryRuntimeEvents::Sequence = 0;

FString UFoundryRuntimeEvents::RunId()
{
    FString Value;
    if (FParse::Value(FCommandLine::Get(), TEXT("FoundryRunId="), Value) && !Value.IsEmpty())
    {
        return Value;
    }
    return TEXT("unknown");
}

FString UFoundryRuntimeEvents::Scenario()
{
    FString Value;
    if (FParse::Value(FCommandLine::Get(), TEXT("FoundryScenario="), Value) && !Value.IsEmpty())
    {
        return Value;
    }
    return TEXT("unknown");
}

void UFoundryRuntimeEvents::Emit(const UObject* Context, const TCHAR* Event, const FString& Fields)
{
    ++Sequence;
    const UWorld* World = Context ? Context->GetWorld() : nullptr;
    const FString WorldName = GetNameSafe(World);
    const FString MapName = World ? World->GetMapName() : FString(TEXT("None"));
    const uint64 Frame = GFrameCounter;
    const double TimeSeconds = World ? World->GetTimeSeconds() : 0.0;
    UE_LOG(LogTemp, Display, TEXT("LogFoundryEvent: schema_version=1 run_id=%s scenario=%s sequence=%d event=%s frame=%llu time_seconds=%.3f world=%s map=%s %s"), *RunId(), *Scenario(), Sequence, Event, Frame, TimeSeconds, *WorldName, *MapName, *Fields);
}
