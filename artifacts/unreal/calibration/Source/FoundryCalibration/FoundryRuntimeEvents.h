#pragma once

#include "CoreMinimal.h"
#include "FoundryRuntimeEvents.generated.h"

UCLASS()
class FOUNDRYCALIBRATION_API UFoundryRuntimeEvents : public UObject
{
    GENERATED_BODY()

public:
    static void Emit(const UObject* Context, const TCHAR* Event, const FString& Fields = FString());
    static FString RunId();
    static FString Scenario();

private:
    static int32 Sequence;
};
