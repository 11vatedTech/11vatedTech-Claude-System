#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "FoundryRelicActor.generated.h"

UENUM(BlueprintType)
enum class ERelicPulseState : uint8
{
    Dormant,
    Reading,
    SafeWindow,
    Hostile,
    Cooled
};

class UNiagaraComponent;
class UNiagaraSystem;
class UPointLightComponent;
class USoundBase;
class UAnimationAsset;

UCLASS()
class FOUNDRYCALIBRATION_API AFoundryRelicActor : public AActor
{
    GENERATED_BODY()

public:
    AFoundryRelicActor();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Foundry|Relic")
    TObjectPtr<USkeletalMeshComponent> RelicMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Foundry|Audio")
    TObjectPtr<class USoundBase> FeedbackSound;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Foundry|VFX")
    TObjectPtr<UNiagaraComponent> AttuneVFX;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Foundry|Lighting")
    TObjectPtr<UPointLightComponent> StateLight;

    UPROPERTY()
    TObjectPtr<UNiagaraSystem> AttuneVFXSystem;

    UPROPERTY()
    TObjectPtr<USoundBase> SafeWindowSound;

    UPROPERTY()
    TObjectPtr<USoundBase> HostileSound;

    UPROPERTY()
    TObjectPtr<USoundBase> SuccessSound;

    UPROPERTY()
    TObjectPtr<USoundBase> RejectSound;

    UPROPERTY()
    TObjectPtr<UAnimationAsset> ReadingAnimation;

    UPROPERTY()
    TObjectPtr<UAnimationAsset> SafeWindowAnimation;

    UPROPERTY()
    TObjectPtr<UAnimationAsset> HostileAnimation;

    UPROPERTY()
    TObjectPtr<UAnimationAsset> SuccessAnimation;

    UPROPERTY(BlueprintReadOnly, Category="Foundry|Relic")
    ERelicPulseState PulseState = ERelicPulseState::Dormant;

    UPROPERTY(BlueprintReadOnly, Category="Foundry|Relic")
    float PulsePhase = 0.0f;

    UFUNCTION(BlueprintCallable, Category="Foundry|Relic")
    bool TryAttune();

    UFUNCTION(BlueprintPure, Category="Foundry|Relic")
    bool IsSafeWindow() const { return PulseState == ERelicPulseState::SafeWindow; }

    UFUNCTION(BlueprintCallable, Category="Foundry|Evidence")
    void ForceEvidenceState(ERelicPulseState NewState);

private:
    float StateTime = 0.0f;
    TArray<TObjectPtr<UMaterialInstanceDynamic>> DynamicMaterials;
    void SetPulseState(ERelicPulseState NewState);
    void ApplyStatePresentation(ERelicPulseState NewState);
    UAnimationAsset* AnimationForState(ERelicPulseState State) const;
    USoundBase* SoundForState(ERelicPulseState State) const;
};
