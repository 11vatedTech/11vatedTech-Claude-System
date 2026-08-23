#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "InputCoreTypes.h"
#include "TimerManager.h"
#include "FoundryGameMode.generated.h"

class UFoundryGameStateComponent;
class AStaticMeshActor;
class UStaticMesh;

UCLASS()
class FOUNDRYCALIBRATION_API AFoundryGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AFoundryGameMode();
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Foundry|State")
    TObjectPtr<UFoundryGameStateComponent> FoundryState;

private:
    int32 InputProofRelicIndex = 0;
    bool bInputProofRestartSent = false;
    FTimerHandle InputProofTimer;
    FTimerHandle VisualProofTimer;
    int32 VisualProofShotIndex = 0;
    FString VisualProofDir;

    void BeginInputProofIfRequested();
    void BeginVisualProofIfRequested();
    void CaptureVisualProofFrame();
    void DriveInputProof();
    void SendInputKeyToPlayer(const FKey& Key);
    void BuildEnvironmentApprenticeshipBlockout(UWorld* World);
    void BuildCinderworksAbbey(UWorld* World);
    void BuildEmberHospice(UWorld* World);
    void BuildFallenSunOrchard(UWorld* World);
    void BuildApprenticeshipLabs(UWorld* World, UStaticMesh* Cube, UStaticMesh* Cylinder, const TCHAR* DirectionLabel, const FVector& Origin);
    void BuildPhase3PerformanceProxy(UWorld* World, UStaticMesh* Cube, UStaticMesh* Cylinder, const TCHAR* DirectionLabel, const FVector& Origin);
    void ApplyPhase3ReviewState(UWorld* World, const TCHAR* DirectionLabel);
    void PlaceRelicStation(UWorld* World, UStaticMesh* Cube, UStaticMesh* Cylinder, const FVector& Location, const TCHAR* RelicLabel, const TCHAR* SupportLabel, const FColor& SupportColor);
    AStaticMeshActor* SpawnMeshActor(UWorld* World, UStaticMesh* Mesh, const FVector& Location, const FRotator& Rotation, const FVector& Scale, const FColor& Color, const TCHAR* Label);
    void AddPointLight(UWorld* World, const FVector& Location, const FLinearColor& Color, float Intensity, float Radius, const TCHAR* Label);
};
