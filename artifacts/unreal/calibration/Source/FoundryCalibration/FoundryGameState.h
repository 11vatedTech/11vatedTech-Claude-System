#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "FoundryGameState.generated.h"

UENUM(BlueprintType)
enum class EFoundryRunState : uint8
{
    Start,
    Playing,
    Success,
    Failure,
    Restart
};

UCLASS(ClassGroup=(Foundry), BlueprintType, Blueprintable, meta=(BlueprintSpawnableComponent))
class FOUNDRYCALIBRATION_API UFoundryGameStateComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFoundryGameStateComponent();

    UPROPERTY(BlueprintReadOnly, Category="Foundry|State")
    EFoundryRunState RunState = EFoundryRunState::Start;

    UPROPERTY(BlueprintReadOnly, Category="Foundry|State")
    int32 LitCoals = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Foundry|State")
    int32 RequiredCoals = 3;

    UFUNCTION(BlueprintCallable, Category="Foundry|State")
    void BeginRun();

    UFUNCTION(BlueprintCallable, Category="Foundry|State")
    bool RegisterAttunement(bool bSafeWindow);

    UFUNCTION(BlueprintCallable, Category="Foundry|State")
    void FailRun();

    UFUNCTION(BlueprintCallable, Category="Foundry|State")
    void RestartRun();
};
