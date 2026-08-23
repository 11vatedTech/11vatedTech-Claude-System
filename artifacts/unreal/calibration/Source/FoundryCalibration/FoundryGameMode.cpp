#include "FoundryGameMode.h"
#include "FoundryGameState.h"
#include "FoundryPlayerCharacter.h"
#include "FoundryRelicActor.h"
#include "FoundryHUD.h"
#include "FoundryRuntimeEvents.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Engine/PointLight.h"
#include "EngineUtils.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "GameFramework/PlayerInput.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

AFoundryGameMode::AFoundryGameMode()
{
    DefaultPawnClass = AFoundryPlayerCharacter::StaticClass();
    HUDClass = AFoundryHUD::StaticClass();
    FoundryState = CreateDefaultSubobject<UFoundryGameStateComponent>(TEXT("FoundryState"));
}

void AFoundryGameMode::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_MAP_BEGINPLAY World=%s"), *GetNameSafe(GetWorld()));
    UFoundryRuntimeEvents::Emit(this, TEXT("MAP_LOADED"), FString::Printf(TEXT("world=%s"), *GetNameSafe(GetWorld())));
    FoundryState->BeginRun();
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_GAMEPLAY_BEGIN RequiredCoals=%d"), FoundryState->RequiredCoals);
    UFoundryRuntimeEvents::Emit(this, TEXT("GAMEPLAY_BEGIN"), FString::Printf(TEXT("required_coals=%d"), FoundryState->RequiredCoals));
    if (UWorld* World = GetWorld())
    {
        BuildEnvironmentApprenticeshipBlockout(World);
    }
    BeginVisualProofIfRequested();
    BeginInputProofIfRequested();
}

AStaticMeshActor* AFoundryGameMode::SpawnMeshActor(UWorld* World, UStaticMesh* Mesh, const FVector& Location, const FRotator& Rotation, const FVector& Scale, const FColor& Color, const TCHAR* Label)
{
    if (!World || !Mesh)
    {
        return nullptr;
    }
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(Location, Rotation, Params);
    if (!Actor)
    {
        return nullptr;
    }
    Actor->SetActorScale3D(Scale);
    Actor->Tags.Add(FName(Label));
    UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
    Component->SetStaticMesh(Mesh);
    Component->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    if (UMaterialInterface* BaseMaterial = Component->GetMaterial(0))
    {
        if (UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, Component))
        {
            Material->SetVectorParameterValue(TEXT("BaseColor"), FLinearColor(Color));
            Material->SetVectorParameterValue(TEXT("Color"), FLinearColor(Color));
            Material->SetScalarParameterValue(TEXT("EmberIntensity"), Color.R > 90 ? 1.6f : 0.15f);
            Component->SetMaterial(0, Material);
        }
    }
    Component->SetCustomPrimitiveDataFloat(0, Color.R / 255.0f);
    Component->SetCustomPrimitiveDataFloat(1, Color.G / 255.0f);
    Component->SetCustomPrimitiveDataFloat(2, Color.B / 255.0f);
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_ENV_ASSET label=%s location=(%.1f,%.1f,%.1f) scale=(%.1f,%.1f,%.1f) color=(%d,%d,%d)"), Label, Location.X, Location.Y, Location.Z, Scale.X, Scale.Y, Scale.Z, Color.R, Color.G, Color.B);
    UFoundryRuntimeEvents::Emit(this, TEXT("ENVIRONMENT_ASSET"), FString::Printf(TEXT("label=%s location=(%.1f,%.1f,%.1f) scale=(%.1f,%.1f,%.1f)"), Label, Location.X, Location.Y, Location.Z, Scale.X, Scale.Y, Scale.Z));
    return Actor;
}

void AFoundryGameMode::AddPointLight(UWorld* World, const FVector& Location, const FLinearColor& Color, float Intensity, float Radius, const TCHAR* Label)
{
    if (!World)
    {
        return;
    }
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    if (APointLight* Light = World->SpawnActor<APointLight>(Location, FRotator::ZeroRotator, Params))
    {
        Light->Tags.Add(FName(Label));
        if (UPointLightComponent* LightComponent = Light->PointLightComponent)
        {
            LightComponent->SetLightColor(Color);
            LightComponent->SetIntensity(Intensity);
            LightComponent->SetAttenuationRadius(Radius);
            LightComponent->SetCastShadows(true);
        }
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_LIGHT label=%s location=(%.1f,%.1f,%.1f) intensity=%.1f radius=%.1f color=(%.2f,%.2f,%.2f)"), Label, Location.X, Location.Y, Location.Z, Intensity, Radius, Color.R, Color.G, Color.B);
        UFoundryRuntimeEvents::Emit(this, TEXT("LIGHTING_SOURCE"), FString::Printf(TEXT("label=%s location=(%.1f,%.1f,%.1f) intensity=%.1f radius=%.1f"), Label, Location.X, Location.Y, Location.Z, Intensity, Radius));
    }
}

void AFoundryGameMode::BuildEnvironmentApprenticeshipBlockout(UWorld* World)
{
    FString Direction;
    FParse::Value(FCommandLine::Get(), TEXT("AshwakeEnvironmentDirection="), Direction);
    if (Direction.Equals(TEXT("EMBER_HOSPICE"), ESearchCase::IgnoreCase))
    {
        BuildEmberHospice(World);
        return;
    }
    if (Direction.Equals(TEXT("FALLEN_SUN_ORCHARD"), ESearchCase::IgnoreCase))
    {
        BuildFallenSunOrchard(World);
        return;
    }
    BuildCinderworksAbbey(World);
}

void AFoundryGameMode::PlaceRelicStation(UWorld* World, UStaticMesh* Cube, UStaticMesh* Cylinder, const FVector& Location, const TCHAR* RelicLabel, const TCHAR* SupportLabel, const FColor& SupportColor)
{
    SpawnMeshActor(World, Cube, Location + FVector(0.0f, 0.0f, -72.0f), FRotator::ZeroRotator, FVector(1.8f, 1.2f, 0.34f), SupportColor, SupportLabel);
    SpawnMeshActor(World, Cylinder, Location + FVector(0.0f, 0.0f, -6.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(1.15f, 1.15f, 0.22f), FColor(116, 76, 34), TEXT("Physical reliquary retaining ring"));
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    if (AFoundryRelicActor* Relic = World->SpawnActor<AFoundryRelicActor>(Location, FRotator(0.0f, 180.0f, 0.0f), Params))
    {
        Relic->SetActorScale3D(FVector(1.05f));
        Relic->Tags.Add(FName(RelicLabel));
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_RELIQUARY_PLACED label=%s location=(%.1f,%.1f,%.1f) embedded=true phase=environment_apprenticeship_blockout"), RelicLabel, Location.X, Location.Y, Location.Z);
        UFoundryRuntimeEvents::Emit(this, TEXT("RELIQUARY_PLACED"), FString::Printf(TEXT("label=%s embedded=true phase=environment_apprenticeship_blockout"), RelicLabel));
    }
}

void AFoundryGameMode::BuildApprenticeshipLabs(UWorld* World, UStaticMesh* Cube, UStaticMesh* Cylinder, const TCHAR* DirectionLabel, const FVector& Origin)
{
    const TCHAR* LightingLabels[] = {
        TEXT("Lighting Variant A emissive dominant"),
        TEXT("Lighting Variant B motivated key fill"),
        TEXT("Lighting Variant C environment bounce dominant"),
        TEXT("Lighting Variant D volumetric atmosphere proxy"),
        TEXT("Lighting Variant E readable low key cinematic"),
        TEXT("Lighting Variant F altered value hierarchy")
    };
    const FLinearColor LightingColors[] = {
        FLinearColor(1.0f, 0.32f, 0.08f),
        FLinearColor(0.95f, 0.68f, 0.42f),
        FLinearColor(0.34f, 0.48f, 0.76f),
        FLinearColor(0.62f, 0.54f, 0.82f),
        FLinearColor(0.95f, 0.50f, 0.18f),
        FLinearColor(0.18f, 0.74f, 1.0f)
    };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(LightingLabels); ++Index)
    {
        const FVector Station = Origin + FVector(Index * 190.0f, 900.0f, 0.0f);
        SpawnMeshActor(World, Cube, Station + FVector(0.0f, 0.0f, -96.0f), FRotator::ZeroRotator, FVector(1.25f, 1.25f, 0.06f), FColor(38, 35, 32), LightingLabels[Index]);
        SpawnMeshActor(World, Cube, Station + FVector(0.0f, 0.0f, 80.0f), FRotator::ZeroRotator, FVector(0.28f, 0.28f, 1.4f), FColor(76, 68, 58), TEXT("Lighting readability pillar"));
        AddPointLight(World, Station + FVector(0.0f, 0.0f, 260.0f), LightingColors[Index], Index == 4 ? 700.0f : 1700.0f + Index * 280.0f, 360.0f + Index * 50.0f, LightingLabels[Index]);
    }

    const FColor Materials[] = {
        FColor(28, 26, 24), FColor(92, 64, 38), FColor(116, 82, 44), FColor(38, 33, 29), FColor(170, 116, 58)
    };
    const TCHAR* MaterialLabels[] = {
        TEXT("Material study structural dark mass"),
        TEXT("Material study heat treated metal"),
        TEXT("Material study sacred worn surface"),
        TEXT("Material study ash soot deposit"),
        TEXT("Material study focal ember material")
    };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(MaterialLabels); ++Index)
    {
        SpawnMeshActor(World, Cube, Origin + FVector(Index * 155.0f, 1120.0f, -42.0f), FRotator::ZeroRotator, FVector(0.95f, 0.95f, 0.12f), Materials[Index], MaterialLabels[Index]);
        SpawnMeshActor(World, Cylinder, Origin + FVector(Index * 155.0f, 1120.0f, 70.0f), FRotator::ZeroRotator, FVector(0.55f, 0.55f, 0.75f), Materials[Index], TEXT("Material response cylinder"));
    }

    const TCHAR* StateLabels[] = {
        TEXT("State lab READING dim rhythm proxy"),
        TEXT("State lab SAFE widened pulse proxy"),
        TEXT("State lab HOSTILE jagged distress proxy"),
        TEXT("State lab SUCCESS environment response proxy"),
        TEXT("State lab FAILURE retreating light proxy")
    };
    const FColor StateColors[] = {
        FColor(84, 42, 18), FColor(255, 162, 46), FColor(255, 18, 12), FColor(46, 190, 255), FColor(36, 26, 22)
    };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(StateLabels); ++Index)
    {
        const FVector Station = Origin + FVector(Index * 170.0f, 1320.0f, 0.0f);
        SpawnMeshActor(World, Cube, Station + FVector(0.0f, 0.0f, -70.0f), FRotator::ZeroRotator, FVector(1.05f, 0.16f + Index * 0.06f, 0.08f), StateColors[Index], StateLabels[Index]);
        SpawnMeshActor(World, Cylinder, Station + FVector(0.0f, 0.0f, 60.0f + Index * 10.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(0.26f + Index * 0.04f, 0.26f + Index * 0.04f, 0.30f), StateColors[Index], TEXT("State feedback motion silhouette proxy"));
    }

    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_APPRENTICESHIP_LABS Direction=%s LightingVariants=6 MaterialStudies=5 StateStudies=5 BlockoutOnly=true"), DirectionLabel);
    UFoundryRuntimeEvents::Emit(this, TEXT("APPRENTICESHIP_LABS_READY"), FString::Printf(TEXT("direction=%s lighting_variants=6 material_studies=5 state_studies=5 blockout_only=true"), DirectionLabel));
}

void AFoundryGameMode::BuildPhase3PerformanceProxy(UWorld* World, UStaticMesh* Cube, UStaticMesh* Cylinder, const TCHAR* DirectionLabel, const FVector& Origin)
{
    if (!World || !Cube || !Cylinder || !FParse::Param(FCommandLine::Get(), TEXT("AshwakePhase3PerformanceProxy")))
    {
        return;
    }

    for (int32 Index = 0; Index < 18; ++Index)
    {
        const float X = Origin.X + (Index % 6) * 210.0f;
        const float Y = Origin.Y - 760.0f + (Index / 6) * 180.0f;
        const float Height = 0.65f + (Index % 4) * 0.32f;
        SpawnMeshActor(World, Cube, FVector(X, Y, -55.0f), FRotator::ZeroRotator, FVector(1.2f, 0.18f, Height), FColor(46 + Index * 3, 42, 36), TEXT("Phase3 representative geometry density proxy"));
    }

    for (int32 Index = 0; Index < 10; ++Index)
    {
        const FVector Station = Origin + FVector(Index * 150.0f, -1040.0f, 40.0f + Index * 8.0f);
        SpawnMeshActor(World, Cylinder, Station, FRotator(90.0f, 0.0f, 0.0f), FVector(0.18f, 0.18f, 1.7f), FColor(86, 112, 118), TEXT("Phase3 glass translucency cost proxy"));
        AddPointLight(World, Station + FVector(0.0f, 0.0f, 180.0f), FLinearColor(0.42f, 0.62f, 0.72f), 260.0f, 250.0f, TEXT("Phase3 small practical proxy"));
    }

    for (int32 Index = 0; Index < 12; ++Index)
    {
        const FVector Station = Origin + FVector(Index * 125.0f, 1540.0f, -35.0f);
        SpawnMeshActor(World, Cube, Station, FRotator::ZeroRotator, FVector(0.82f, 0.08f + (Index % 3) * 0.04f, 0.05f), FColor(150, 76 + Index * 4, 28), TEXT("Phase3 fog particle emissive band proxy"));
    }

    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_PHASE3_PERFORMANCE_PROXY Direction=%s FogParticlesGlassMaterialsGeometryLumenAudio=true GeometryActors=40 ClassificationInput=true"), DirectionLabel);
    UFoundryRuntimeEvents::Emit(this, TEXT("PHASE3_PERFORMANCE_PROXY_READY"), FString::Printf(TEXT("direction=%s fog_particles_glass_materials_geometry_lumen_audio=true"), DirectionLabel));
}

void AFoundryGameMode::ApplyPhase3ReviewState(UWorld* World, const TCHAR* DirectionLabel)
{
    if (!World)
    {
        return;
    }

    FString ReviewState;
    FParse::Value(FCommandLine::Get(), TEXT("AshwakePhase3ReviewState="), ReviewState);
    if (ReviewState.IsEmpty())
    {
        return;
    }

    ERelicPulseState ForcedState = ERelicPulseState::Reading;
    if (ReviewState.Equals(TEXT("SAFE_WINDOW"), ESearchCase::IgnoreCase) || ReviewState.Equals(TEXT("ACCEPTED_INTERACTION"), ESearchCase::IgnoreCase)) ForcedState = ERelicPulseState::SafeWindow;
    else if (ReviewState.Equals(TEXT("HOSTILE"), ESearchCase::IgnoreCase) || ReviewState.Equals(TEXT("REJECTED_INTERACTION"), ESearchCase::IgnoreCase) || ReviewState.Equals(TEXT("FAILURE"), ESearchCase::IgnoreCase)) ForcedState = ERelicPulseState::Hostile;
    else if (ReviewState.Equals(TEXT("ONE_COAL_RESTORED"), ESearchCase::IgnoreCase) || ReviewState.Equals(TEXT("SUCCESS"), ESearchCase::IgnoreCase) || ReviewState.Equals(TEXT("FINAL_CLIMAX_DIRECTION"), ESearchCase::IgnoreCase)) ForcedState = ERelicPulseState::Cooled;

    int32 RelicIndex = 0;
    for (TActorIterator<AFoundryRelicActor> It(World); It; ++It, ++RelicIndex)
    {
        if (ReviewState.Equals(TEXT("ONE_COAL_RESTORED"), ESearchCase::IgnoreCase) && RelicIndex > 0)
        {
            It->ForceEvidenceState(ERelicPulseState::Reading);
        }
        else
        {
            It->ForceEvidenceState(ForcedState);
        }
    }

    if (AFoundryPlayerCharacter* Player = Cast<AFoundryPlayerCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)))
    {
        FVector Location(-300.0f, 0.0f, 42.0f);
        FRotator Rotation(0.0f, 0.0f, 0.0f);
        FRotator ControlRotation(-8.0f, 0.0f, 0.0f);
        if (ReviewState.Equals(TEXT("FIRST_LANDMARK"), ESearchCase::IgnoreCase)) { Location = FVector(-80.0f, -160.0f, 42.0f); ControlRotation = FRotator(-8.0f, 12.0f, 0.0f); }
        else if (ReviewState.Equals(TEXT("APPROACH"), ESearchCase::IgnoreCase)) { Location = FVector(210.0f, -80.0f, 42.0f); ControlRotation = FRotator(-10.0f, 5.0f, 0.0f); }
        else if (ReviewState.Equals(TEXT("READING"), ESearchCase::IgnoreCase)) { Location = FVector(320.0f, -120.0f, 42.0f); ControlRotation = FRotator(-12.0f, 12.0f, 0.0f); }
        else if (ReviewState.Equals(TEXT("SAFE_WINDOW"), ESearchCase::IgnoreCase) || ReviewState.Equals(TEXT("HOSTILE"), ESearchCase::IgnoreCase)) { Location = FVector(620.0f, 120.0f, 42.0f); ControlRotation = FRotator(-12.0f, 20.0f, 0.0f); }
        else if (ReviewState.Equals(TEXT("REJECTED_INTERACTION"), ESearchCase::IgnoreCase) || ReviewState.Equals(TEXT("ACCEPTED_INTERACTION"), ESearchCase::IgnoreCase)) { Location = FVector(760.0f, 100.0f, 42.0f); ControlRotation = FRotator(-14.0f, 18.0f, 0.0f); }
        else if (ReviewState.Equals(TEXT("ONE_COAL_RESTORED"), ESearchCase::IgnoreCase)) { Location = FVector(440.0f, -130.0f, 42.0f); ControlRotation = FRotator(-10.0f, 0.0f, 0.0f); }
        else if (ReviewState.Equals(TEXT("FINAL_CLIMAX_DIRECTION"), ESearchCase::IgnoreCase)) { Location = FVector(950.0f, 0.0f, 42.0f); ControlRotation = FRotator(-12.0f, 0.0f, 0.0f); }
        else if (ReviewState.Equals(TEXT("ENVIRONMENT_OVERVIEW"), ESearchCase::IgnoreCase)) { Location = FVector(240.0f, -520.0f, 220.0f); ControlRotation = FRotator(-20.0f, 28.0f, 0.0f); }
        Player->SetActorLocation(Location, false, nullptr, ETeleportType::TeleportPhysics);
        Player->SetActorRotation(Rotation);
        if (APlayerController* Controller = UGameplayStatics::GetPlayerController(World, 0))
        {
            Controller->SetControlRotation(ControlRotation);
        }
    }

    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_PHASE3_REVIEW_STATE Direction=%s State=%s NoHUD=%s"), DirectionLabel, *ReviewState, FParse::Param(FCommandLine::Get(), TEXT("AshwakeNoHUD")) ? TEXT("true") : TEXT("false"));
    UFoundryRuntimeEvents::Emit(this, TEXT("PHASE3_REVIEW_STATE_READY"), FString::Printf(TEXT("direction=%s state=%s no_hud=%s"), DirectionLabel, *ReviewState, FParse::Param(FCommandLine::Get(), TEXT("AshwakeNoHUD")) ? TEXT("true") : TEXT("false")));
}

void AFoundryGameMode::BuildCinderworksAbbey(UWorld* World)
{
    if (!World || !FoundryState)
    {
        return;
    }
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UStaticMesh* Cylinder = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (!Cube || !Cylinder)
    {
        UE_LOG(LogTemp, Warning, TEXT("LogFoundry: ASHWAKE_ENVIRONMENT_FAILED reason=basic_shape_missing"));
        return;
    }

    SpawnMeshActor(World, Cube, FVector(520.0f, 0.0f, -135.0f), FRotator::ZeroRotator, FVector(16.0f, 11.0f, 0.16f), FColor(42, 38, 32), TEXT("Cinderworks ash-settling floor"));
    SpawnMeshActor(World, Cube, FVector(520.0f, -620.0f, 40.0f), FRotator::ZeroRotator, FVector(17.0f, 0.26f, 3.8f), FColor(28, 25, 22), TEXT("Cinderworks north soot wall"));
    SpawnMeshActor(World, Cube, FVector(520.0f, 620.0f, 40.0f), FRotator::ZeroRotator, FVector(17.0f, 0.26f, 3.8f), FColor(28, 25, 22), TEXT("Cinderworks south soot wall"));
    SpawnMeshActor(World, Cube, FVector(-380.0f, 0.0f, 135.0f), FRotator::ZeroRotator, FVector(0.32f, 11.0f, 5.4f), FColor(34, 31, 28), TEXT("Collapsed abbey entry mass"));
    SpawnMeshActor(World, Cube, FVector(1420.0f, 0.0f, 135.0f), FRotator::ZeroRotator, FVector(0.32f, 11.0f, 5.4f), FColor(34, 31, 28), TEXT("Furnace apse wall"));

    for (int32 Index = 0; Index < 6; ++Index)
    {
        const float X = -160.0f + Index * 270.0f;
        SpawnMeshActor(World, Cube, FVector(X, -430.0f, 170.0f), FRotator::ZeroRotator, FVector(0.34f, 0.34f, 4.2f), FColor(48, 43, 36), TEXT("North ribbed heat column"));
        SpawnMeshActor(World, Cube, FVector(X, 430.0f, 170.0f), FRotator::ZeroRotator, FVector(0.34f, 0.34f, 4.2f), FColor(48, 43, 36), TEXT("South ribbed heat column"));
        SpawnMeshActor(World, Cube, FVector(X, 0.0f, 560.0f), FRotator(0.0f, 0.0f, 18.0f), FVector(0.18f, 9.2f, 0.28f), FColor(56, 48, 40), TEXT("Cinderworks furnace rib vault"));
    }

    SpawnMeshActor(World, Cube, FVector(520.0f, 0.0f, -92.0f), FRotator::ZeroRotator, FVector(13.5f, 0.20f, 0.05f), FColor(180, 94, 24), TEXT("Main gold-leaf heat seam"));
    SpawnMeshActor(World, Cube, FVector(520.0f, -220.0f, -90.0f), FRotator(0.0f, 0.0f, 0.0f), FVector(12.5f, 0.08f, 0.06f), FColor(122, 61, 18), TEXT("North ember flue line"));
    SpawnMeshActor(World, Cube, FVector(520.0f, 220.0f, -90.0f), FRotator(0.0f, 0.0f, 0.0f), FVector(12.5f, 0.08f, 0.06f), FColor(122, 61, 18), TEXT("South ember flue line"));
    SpawnMeshActor(World, Cube, FVector(1220.0f, 0.0f, -78.0f), FRotator::ZeroRotator, FVector(2.8f, 3.2f, 0.18f), FColor(100, 44, 14), TEXT("Furnace throat glow bed"));

    const FVector RelicLocations[] = {FVector(0.0f, -260.0f, 70.0f), FVector(620.0f, 300.0f, 95.0f), FVector(1220.0f, 0.0f, 130.0f)};
    const TCHAR* RelicLabels[] = {TEXT("Intake Reliquary Ash Gate Kiln"), TEXT("Balance Reliquary Cloister Cistern"), TEXT("Heart Reliquary Furnace Nave Apse")};
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    const int32 RelicCount = FMath::Min(FoundryState->RequiredCoals, static_cast<int32>(UE_ARRAY_COUNT(RelicLocations)));
    for (int32 Index = 0; Index < RelicCount; ++Index)
    {
        const FVector RelicLocation = RelicLocations[Index];
        SpawnMeshActor(World, Cube, RelicLocation + FVector(0.0f, 0.0f, -72.0f), FRotator::ZeroRotator, FVector(1.8f, 1.2f, 0.34f), FColor(68, 50, 28), TEXT("Embedded reliquary cradle"));
        SpawnMeshActor(World, Cylinder, RelicLocation + FVector(0.0f, 0.0f, -6.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(1.15f, 1.15f, 0.22f), FColor(116, 76, 34), TEXT("Brass reliquary retaining ring"));
        if (AFoundryRelicActor* Relic = World->SpawnActor<AFoundryRelicActor>(RelicLocation, FRotator(0.0f, 180.0f, 0.0f), Params))
        {
            Relic->SetActorScale3D(FVector(1.05f));
            Relic->Tags.Add(FName(RelicLabels[Index]));
            UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_RELIQUARY_PLACED index=%d label=%s location=(%.1f,%.1f,%.1f) embedded=true"), Index, RelicLabels[Index], RelicLocation.X, RelicLocation.Y, RelicLocation.Z);
            UFoundryRuntimeEvents::Emit(this, TEXT("RELIQUARY_PLACED"), FString::Printf(TEXT("index=%d label=%s embedded=true"), Index, RelicLabels[Index]));
        }
    }

    for (int32 Index = 0; Index < 5; ++Index)
    {
        const float Y = -330.0f + Index * 165.0f;
        SpawnMeshActor(World, Cylinder, FVector(1160.0f, Y, 330.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(0.055f, 0.055f, 7.0f), FColor(96, 72, 38), TEXT("Bell cable timing line"));
    }

    AddPointLight(World, FVector(-160.0f, -320.0f, 460.0f), FLinearColor(0.48f, 0.60f, 0.78f), 900.0f, 900.0f, TEXT("Cold ash clerestory key"));
    AddPointLight(World, FVector(1220.0f, 0.0f, 50.0f), FLinearColor(1.0f, 0.34f, 0.08f), 3600.0f, 1050.0f, TEXT("Low furnace bounce"));
    AddPointLight(World, FVector(520.0f, -460.0f, 240.0f), FLinearColor(0.82f, 0.56f, 0.30f), 850.0f, 700.0f, TEXT("North brass rim practical"));
    AddPointLight(World, FVector(520.0f, 460.0f, 240.0f), FLinearColor(0.82f, 0.56f, 0.30f), 850.0f, 700.0f, TEXT("South brass rim practical"));
    BuildApprenticeshipLabs(World, Cube, Cylinder, TEXT("CINDERWORKS_ABBEY"), FVector(-180.0f, 0.0f, 0.0f));
    BuildPhase3PerformanceProxy(World, Cube, Cylinder, TEXT("CINDERWORKS_ABBEY"), FVector(-180.0f, 0.0f, 0.0f));

    if (AFoundryPlayerCharacter* Player = Cast<AFoundryPlayerCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)))
    {
        Player->SetActorLocation(FVector(-260.0f, 0.0f, 42.0f), false, nullptr, ETeleportType::TeleportPhysics);
        Player->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
        if (APlayerController* Controller = UGameplayStatics::GetPlayerController(World, 0))
        {
            Controller->SetControlRotation(FRotator(-8.0f, 0.0f, 0.0f));
        }
    }

    ApplyPhase3ReviewState(World, TEXT("CINDERWORKS_ABBEY"));
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_ENVIRONMENT Direction=CinderworksAbbey Layout=AbbeyForge Reliquaries=3 TestChamber=false"));
    UFoundryRuntimeEvents::Emit(this, TEXT("ENVIRONMENT_READY"), TEXT("direction=CinderworksAbbey layout=AbbeyForge reliquaries=3 test_chamber=false"));
}

void AFoundryGameMode::BuildEmberHospice(UWorld* World)
{
    if (!World || !FoundryState)
    {
        return;
    }
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UStaticMesh* Cylinder = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (!Cube || !Cylinder)
    {
        UE_LOG(LogTemp, Warning, TEXT("LogFoundry: ASHWAKE_ENVIRONMENT_FAILED reason=basic_shape_missing"));
        return;
    }

    SpawnMeshActor(World, Cube, FVector(540.0f, 0.0f, -135.0f), FRotator::ZeroRotator, FVector(18.0f, 8.0f, 0.16f), FColor(62, 58, 52), TEXT("Hospice ward floor blockout"));
    SpawnMeshActor(World, Cube, FVector(-240.0f, 0.0f, 90.0f), FRotator::ZeroRotator, FVector(0.28f, 7.6f, 4.4f), FColor(54, 50, 46), TEXT("Hospice intake threshold"));
    SpawnMeshActor(World, Cube, FVector(540.0f, -440.0f, 70.0f), FRotator::ZeroRotator, FVector(18.0f, 0.22f, 3.4f), FColor(76, 70, 62), TEXT("Hospice north ward wall"));
    SpawnMeshActor(World, Cube, FVector(540.0f, 440.0f, 70.0f), FRotator::ZeroRotator, FVector(18.0f, 0.22f, 3.4f), FColor(76, 70, 62), TEXT("Hospice south ward wall"));
    SpawnMeshActor(World, Cube, FVector(1480.0f, 0.0f, 130.0f), FRotator::ZeroRotator, FVector(0.30f, 8.0f, 5.2f), FColor(48, 42, 38), TEXT("Life support engine back wall"));

    for (int32 Index = 0; Index < 5; ++Index)
    {
        const float X = 120.0f + Index * 245.0f;
        SpawnMeshActor(World, Cube, FVector(X, -250.0f, -72.0f), FRotator::ZeroRotator, FVector(1.65f, 0.52f, 0.22f), FColor(94, 82, 68), TEXT("Hospice patient cot rhythm north"));
        SpawnMeshActor(World, Cube, FVector(X, 250.0f, -72.0f), FRotator::ZeroRotator, FVector(1.65f, 0.52f, 0.22f), FColor(94, 82, 68), TEXT("Hospice patient cot rhythm south"));
        SpawnMeshActor(World, Cube, FVector(X, 0.0f, 190.0f), FRotator::ZeroRotator, FVector(0.10f, 7.2f, 2.4f), FColor(42, 38, 34), TEXT("Hospice privacy rail sightline"));
    }

    SpawnMeshActor(World, Cube, FVector(540.0f, 0.0f, -88.0f), FRotator::ZeroRotator, FVector(14.2f, 0.13f, 0.06f), FColor(190, 114, 28), TEXT("Amber quarantine route strip"));
    SpawnMeshActor(World, Cube, FVector(1040.0f, 0.0f, 120.0f), FRotator::ZeroRotator, FVector(0.18f, 6.2f, 2.2f), FColor(76, 112, 94), TEXT("Observation glass partition proxy"));
    SpawnMeshActor(World, Cylinder, FVector(1340.0f, -170.0f, 220.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(0.12f, 0.12f, 4.2f), FColor(136, 92, 46), TEXT("Coal lung pipe organ left"));
    SpawnMeshActor(World, Cylinder, FVector(1340.0f, 170.0f, 220.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(0.12f, 0.12f, 4.2f), FColor(136, 92, 46), TEXT("Coal lung pipe organ right"));

    const FVector RelicLocations[] = {FVector(0.0f, -120.0f, 70.0f), FVector(680.0f, 220.0f, 95.0f), FVector(1340.0f, 0.0f, 130.0f)};
    const TCHAR* RelicLabels[] = {TEXT("Triage Reliquary Intake Ward"), TEXT("Graft Reliquary Surgical Chapel"), TEXT("Choir Reliquary Life Support Engine")};
    const int32 RelicCount = FMath::Min(FoundryState->RequiredCoals, static_cast<int32>(UE_ARRAY_COUNT(RelicLocations)));
    for (int32 Index = 0; Index < RelicCount; ++Index)
    {
        PlaceRelicStation(World, Cube, Cylinder, RelicLocations[Index], RelicLabels[Index], TEXT("Hospice cradle clamp life support"), FColor(82, 62, 48));
        SpawnMeshActor(World, Cube, RelicLocations[Index] + FVector(-90.0f, 0.0f, 72.0f), FRotator::ZeroRotator, FVector(0.12f, 1.4f, 0.08f), FColor(180, 46, 24), TEXT("Reliquary pressure pulse tube"));
    }

    AddPointLight(World, FVector(60.0f, -300.0f, 260.0f), FLinearColor(0.34f, 0.42f, 0.56f), 750.0f, 620.0f, TEXT("Cold failing ward key"));
    AddPointLight(World, FVector(680.0f, 220.0f, 160.0f), FLinearColor(1.0f, 0.22f, 0.08f), 2600.0f, 680.0f, TEXT("Coal red patient pulse"));
    AddPointLight(World, FVector(1340.0f, 0.0f, 180.0f), FLinearColor(1.0f, 0.55f, 0.20f), 3100.0f, 850.0f, TEXT("Amber life support route state"));
    AddPointLight(World, FVector(1040.0f, -260.0f, 240.0f), FLinearColor(0.35f, 0.80f, 0.54f), 520.0f, 420.0f, TEXT("Weak diagnostic green practical"));
    BuildApprenticeshipLabs(World, Cube, Cylinder, TEXT("EMBER_HOSPICE"), FVector(-180.0f, 0.0f, 0.0f));
    BuildPhase3PerformanceProxy(World, Cube, Cylinder, TEXT("EMBER_HOSPICE"), FVector(-180.0f, 0.0f, 0.0f));

    if (AFoundryPlayerCharacter* Player = Cast<AFoundryPlayerCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)))
    {
        Player->SetActorLocation(FVector(-260.0f, 0.0f, 42.0f), false, nullptr, ETeleportType::TeleportPhysics);
        Player->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
        if (APlayerController* Controller = UGameplayStatics::GetPlayerController(World, 0))
        {
            Controller->SetControlRotation(FRotator(-8.0f, 0.0f, 0.0f));
        }
    }

    ApplyPhase3ReviewState(World, TEXT("EMBER_HOSPICE"));
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_ENVIRONMENT Direction=EmberHospice Layout=QuarantineWard Reliquaries=3 TestChamber=false BlockoutOnly=true"));
    UFoundryRuntimeEvents::Emit(this, TEXT("ENVIRONMENT_READY"), TEXT("direction=EmberHospice layout=QuarantineWard reliquaries=3 test_chamber=false blockout_only=true"));
}

void AFoundryGameMode::BuildFallenSunOrchard(UWorld* World)
{
    if (!World || !FoundryState)
    {
        return;
    }
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UStaticMesh* Cylinder = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (!Cube || !Cylinder)
    {
        UE_LOG(LogTemp, Warning, TEXT("LogFoundry: ASHWAKE_ENVIRONMENT_FAILED reason=basic_shape_missing"));
        return;
    }

    SpawnMeshActor(World, Cube, FVector(640.0f, 0.0f, -150.0f), FRotator::ZeroRotator, FVector(22.0f, 12.0f, 0.16f), FColor(84, 78, 66), TEXT("Orchard ash dune ground plane"));
    SpawnMeshActor(World, Cube, FVector(640.0f, 0.0f, -92.0f), FRotator::ZeroRotator, FVector(17.5f, 0.12f, 0.05f), FColor(190, 148, 54), TEXT("Buried meridian path line"));
    SpawnMeshActor(World, Cube, FVector(1600.0f, 0.0f, 130.0f), FRotator(0.0f, 0.0f, -16.0f), FVector(0.36f, 4.8f, 5.6f), FColor(36, 32, 28), TEXT("Buried solar colossus silhouette"));

    for (int32 Index = 0; Index < 7; ++Index)
    {
        const float X = -100.0f + Index * 260.0f;
        SpawnMeshActor(World, Cylinder, FVector(X, -340.0f, 60.0f), FRotator(0.0f, 0.0f, 8.0f), FVector(0.34f, 0.34f, 2.6f), FColor(34, 30, 26), TEXT("Vitrified orchard trunk north"));
        SpawnMeshActor(World, Cylinder, FVector(X + 80.0f, 340.0f, 60.0f), FRotator(0.0f, 0.0f, -10.0f), FVector(0.32f, 0.32f, 2.4f), FColor(34, 30, 26), TEXT("Vitrified orchard trunk south"));
        SpawnMeshActor(World, Cube, FVector(X, 0.0f, -86.0f), FRotator::ZeroRotator, FVector(0.08f, 7.2f, 0.06f), FColor(124, 72, 28), TEXT("Root glow timing rib"));
    }

    SpawnMeshActor(World, Cylinder, FVector(420.0f, 0.0f, 120.0f), FRotator(0.0f, 0.0f, 68.0f), FVector(0.50f, 0.50f, 4.8f), FColor(42, 34, 26), TEXT("Split sun tree first landmark"));
    SpawnMeshActor(World, Cube, FVector(920.0f, 0.0f, 30.0f), FRotator(0.0f, 0.0f, -9.0f), FVector(4.2f, 0.24f, 0.20f), FColor(74, 66, 58), TEXT("Collapsed bell causeway second landmark"));
    SpawnMeshActor(World, Cylinder, FVector(1320.0f, -120.0f, 250.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(0.09f, 0.09f, 5.2f), FColor(72, 60, 44), TEXT("Observatory rib climb proxy"));
    SpawnMeshActor(World, Cylinder, FVector(1320.0f, 120.0f, 250.0f), FRotator(90.0f, 0.0f, 0.0f), FVector(0.09f, 0.09f, 5.2f), FColor(72, 60, 44), TEXT("Observatory rib climb proxy"));

    const FVector RelicLocations[] = {FVector(360.0f, -120.0f, 70.0f), FVector(920.0f, 160.0f, 95.0f), FVector(1540.0f, 0.0f, 160.0f)};
    const TCHAR* RelicLabels[] = {TEXT("Root Reliquary Split Sun Tree"), TEXT("Bell Reliquary Collapsed Causeway"), TEXT("Crown Reliquary Buried Solar Colossus")};
    const int32 RelicCount = FMath::Min(FoundryState->RequiredCoals, static_cast<int32>(UE_ARRAY_COUNT(RelicLocations)));
    for (int32 Index = 0; Index < RelicCount; ++Index)
    {
        PlaceRelicStation(World, Cube, Cylinder, RelicLocations[Index], RelicLabels[Index], TEXT("Orchard rooted reliquary socket"), FColor(54, 44, 30));
        SpawnMeshActor(World, Cube, RelicLocations[Index] + FVector(0.0f, 0.0f, -86.0f), FRotator::ZeroRotator, FVector(2.8f, 0.10f, 0.05f), FColor(220, 132, 28), TEXT("Converging root pulse read"));
    }

    AddPointLight(World, FVector(1600.0f, -280.0f, 420.0f), FLinearColor(0.42f, 0.32f, 0.22f), 950.0f, 1200.0f, TEXT("Copper eclipse sky proxy"));
    AddPointLight(World, FVector(420.0f, 0.0f, 80.0f), FLinearColor(1.0f, 0.38f, 0.08f), 1800.0f, 720.0f, TEXT("Root ember first false dawn"));
    AddPointLight(World, FVector(1540.0f, 0.0f, 260.0f), FLinearColor(1.0f, 0.72f, 0.24f), 3400.0f, 1120.0f, TEXT("Crown reliquary false dawn response"));
    AddPointLight(World, FVector(920.0f, 160.0f, 150.0f), FLinearColor(0.80f, 0.52f, 0.26f), 1200.0f, 620.0f, TEXT("Bell causeway shadow alignment practical"));
    BuildApprenticeshipLabs(World, Cube, Cylinder, TEXT("FALLEN_SUN_ORCHARD"), FVector(-180.0f, 0.0f, 0.0f));
    BuildPhase3PerformanceProxy(World, Cube, Cylinder, TEXT("FALLEN_SUN_ORCHARD"), FVector(-180.0f, 0.0f, 0.0f));

    if (AFoundryPlayerCharacter* Player = Cast<AFoundryPlayerCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)))
    {
        Player->SetActorLocation(FVector(-300.0f, 0.0f, 42.0f), false, nullptr, ETeleportType::TeleportPhysics);
        Player->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
        if (APlayerController* Controller = UGameplayStatics::GetPlayerController(World, 0))
        {
            Controller->SetControlRotation(FRotator(-6.0f, 0.0f, 0.0f));
        }
    }

    ApplyPhase3ReviewState(World, TEXT("FALLEN_SUN_ORCHARD"));
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_ENVIRONMENT Direction=FallenSunOrchard Layout=OpenAirPilgrimageLoop Reliquaries=3 TestChamber=false BlockoutOnly=true"));
    UFoundryRuntimeEvents::Emit(this, TEXT("ENVIRONMENT_READY"), TEXT("direction=FallenSunOrchard layout=OpenAirPilgrimageLoop reliquaries=3 test_chamber=false blockout_only=true"));
}

void AFoundryGameMode::BeginVisualProofIfRequested()
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("AshwakeVisualProof")))
    {
        return;
    }

    VisualProofShotIndex = 0;
    FString Dir;
    if (FParse::Value(FCommandLine::Get(), TEXT("AshwakeVisualProofDir="), Dir) && !Dir.IsEmpty())
    {
        VisualProofDir = Dir;
    }
    else
    {
        VisualProofDir = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), TEXT("AshwakeVisualProof"));
    }
    IFileManager::Get().MakeDirectory(*VisualProofDir, true);
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: VISUAL_PROOF_BEGIN Dir=%s"), *VisualProofDir);
    UFoundryRuntimeEvents::Emit(this, TEXT("VISUAL_PROOF_BEGIN"), FString::Printf(TEXT("dir=%s"), *VisualProofDir));
    GetWorldTimerManager().SetTimer(VisualProofTimer, this, &AFoundryGameMode::CaptureVisualProofFrame, 0.75f, true, 0.75f);
}

void AFoundryGameMode::CaptureVisualProofFrame()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    const FString Filename = FPaths::Combine(VisualProofDir, FString::Printf(TEXT("ashwake-gameplay-%02d.png"), VisualProofShotIndex));
    FScreenshotRequest::RequestScreenshot(Filename, true, false, false);
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: SCREENSHOT_REQUESTED Index=%d File=%s"), VisualProofShotIndex, *Filename);
    UFoundryRuntimeEvents::Emit(this, TEXT("SCREENSHOT_REQUESTED"), FString::Printf(TEXT("index=%d file=%s"), VisualProofShotIndex, *Filename));
    ++VisualProofShotIndex;

    int32 MaxShots = 4;
    FParse::Value(FCommandLine::Get(), TEXT("AshwakeVisualProofShots="), MaxShots);
    if (VisualProofShotIndex >= MaxShots)
    {
        GetWorldTimerManager().ClearTimer(VisualProofTimer);
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: VISUAL_PROOF_REQUESTS_COMPLETE Shots=%d Dir=%s"), VisualProofShotIndex, *VisualProofDir);
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: VISUAL_PROOF_COMPLETE Shots=%d Dir=%s"), VisualProofShotIndex, *VisualProofDir);
        UFoundryRuntimeEvents::Emit(this, TEXT("VISUAL_PROOF_REQUESTS_COMPLETE"), FString::Printf(TEXT("shots=%d dir=%s"), VisualProofShotIndex, *VisualProofDir));
        if (FParse::Param(FCommandLine::Get(), TEXT("AshwakeVisualProofExit")))
        {
            // Delay exit so the queued screenshot flushes to disk before shutdown
            // (editor-mode shutdown can stall DDC work and drop the pending PNG).
            FTimerHandle ExitHandle;
            GetWorldTimerManager().SetTimer(ExitHandle, FTimerDelegate::CreateWeakLambda(this, []()
            {
                UE_LOG(LogTemp, Display, TEXT("LogFoundry: EXIT_REQUESTED reason=VisualProofComplete status=0"));
                if (GEngine)
                {
                    GEngine->Exec(nullptr, TEXT("FLUSHDEBUGDRAWING"));
                }
                FPlatformMisc::RequestExitWithStatus(false, 0, TEXT("AshwakeVisualProofExit"));
            }), 1.2f, false);
            UE_LOG(LogTemp, Display, TEXT("LogFoundry: EXIT_SCHEDULED reason=VisualProofComplete delay_seconds=1.2 status=0"));
            UFoundryRuntimeEvents::Emit(this, TEXT("EXIT_SCHEDULED"), TEXT("reason=VisualProofComplete delay_seconds=1.2 status=0"));
        }
    }
}

void AFoundryGameMode::BeginInputProofIfRequested()
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("AshwakeInputProof")))
    {
        return;
    }

    InputProofRelicIndex = 0;
    bInputProofRestartSent = false;
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_BEGIN Source=CommandLine"));
    UFoundryRuntimeEvents::Emit(this, TEXT("INPUT_PROOF_BEGIN"), TEXT("source=CommandLine"));
    GetWorldTimerManager().SetTimer(InputProofTimer, this, &AFoundryGameMode::DriveInputProof, 0.25f, true, 0.25f);
}

void AFoundryGameMode::DriveInputProof()
{
    UWorld* World = GetWorld();
    if (!World || !FoundryState)
    {
        return;
    }

    AFoundryPlayerCharacter* Player = Cast<AFoundryPlayerCharacter>(UGameplayStatics::GetPlayerPawn(World, 0));
    if (!Player)
    {
        return;
    }

    if (FoundryState->RunState == EFoundryRunState::Success)
    {
        if (!bInputProofRestartSent)
        {
            bInputProofRestartSent = true;
            SendInputKeyToPlayer(EKeys::R);
            return;
        }
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_COMPLETE Result=SuccessAndRestart LitCoals=%d RequiredCoals=%d"), FoundryState->LitCoals, FoundryState->RequiredCoals);
        UFoundryRuntimeEvents::Emit(this, TEXT("SUCCESS"), FString::Printf(TEXT("result=SuccessAndRestart lit_coals=%d required_coals=%d"), FoundryState->LitCoals, FoundryState->RequiredCoals));
        GetWorldTimerManager().ClearTimer(InputProofTimer);
        if (FParse::Param(FCommandLine::Get(), TEXT("AshwakeInputProofExit")))
        {
            UE_LOG(LogTemp, Display, TEXT("LogFoundry: EXIT_REQUESTED reason=InputProofComplete status=0"));
            UFoundryRuntimeEvents::Emit(this, TEXT("EXIT_REQUESTED"), TEXT("reason=InputProofComplete status=0"));
            FPlatformMisc::RequestExitWithStatus(false, 0, TEXT("AshwakeInputProofExit"));
        }
        return;
    }

    if (FoundryState->RunState == EFoundryRunState::Failure)
    {
        if (!bInputProofRestartSent)
        {
            bInputProofRestartSent = true;
            SendInputKeyToPlayer(EKeys::R);
            return;
        }
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_COMPLETE Result=FailureAndRestart LitCoals=%d RequiredCoals=%d"), FoundryState->LitCoals, FoundryState->RequiredCoals);
        UFoundryRuntimeEvents::Emit(this, TEXT("FAILURE"), FString::Printf(TEXT("result=FailureAndRestart lit_coals=%d required_coals=%d"), FoundryState->LitCoals, FoundryState->RequiredCoals));
        GetWorldTimerManager().ClearTimer(InputProofTimer);
        if (FParse::Param(FCommandLine::Get(), TEXT("AshwakeInputProofExit")))
        {
            UE_LOG(LogTemp, Display, TEXT("LogFoundry: EXIT_REQUESTED reason=InputProofComplete status=0"));
            UFoundryRuntimeEvents::Emit(this, TEXT("EXIT_REQUESTED"), TEXT("reason=InputProofComplete status=0"));
            FPlatformMisc::RequestExitWithStatus(false, 0, TEXT("AshwakeInputProofExit"));
        }
        return;
    }

    if (bInputProofRestartSent && FoundryState->RunState == EFoundryRunState::Playing && FoundryState->LitCoals == 0)
    {
        const TCHAR* Result = FParse::Param(FCommandLine::Get(), TEXT("AshwakeInputProofFailure")) ? TEXT("FailureAndRestart") : TEXT("SuccessAndRestart");
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_COMPLETE Result=%s LitCoals=%d RequiredCoals=%d"), Result, FoundryState->LitCoals, FoundryState->RequiredCoals);
        UFoundryRuntimeEvents::Emit(this, TEXT("RESTART"), FString::Printf(TEXT("result=%s lit_coals=%d required_coals=%d playable=true"), Result, FoundryState->LitCoals, FoundryState->RequiredCoals));
        GetWorldTimerManager().ClearTimer(InputProofTimer);
        if (FParse::Param(FCommandLine::Get(), TEXT("AshwakeInputProofExit")))
        {
            UE_LOG(LogTemp, Display, TEXT("LogFoundry: EXIT_REQUESTED reason=InputProofComplete status=0"));
            UFoundryRuntimeEvents::Emit(this, TEXT("EXIT_REQUESTED"), TEXT("reason=InputProofComplete status=0"));
            FPlatformMisc::RequestExitWithStatus(false, 0, TEXT("AshwakeInputProofExit"));
        }
        return;
    }

    AFoundryRelicActor* Target = nullptr;
    int32 Index = 0;
    for (TActorIterator<AFoundryRelicActor> It(World); It; ++It, ++Index)
    {
        if (Index == InputProofRelicIndex)
        {
            Target = *It;
            break;
        }
    }

    if (!Target)
    {
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_FAILED Reason=NoRelic Index=%d"), InputProofRelicIndex);
        UFoundryRuntimeEvents::Emit(this, TEXT("FAILURE"), FString::Printf(TEXT("reason=NoRelic index=%d"), InputProofRelicIndex));
        GetWorldTimerManager().ClearTimer(InputProofTimer);
        return;
    }

    Player->SetActorLocation(Target->GetActorLocation() + FVector(80.0f, 0.0f, 0.0f), false, nullptr, ETeleportType::TeleportPhysics);
    const bool bFailureProof = FParse::Param(FCommandLine::Get(), TEXT("AshwakeInputProofFailure"));
    if (bFailureProof && InputProofRelicIndex == 0 && !Target->IsSafeWindow())
    {
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_STEP Mode=Failure Index=%d Relic=%s"), InputProofRelicIndex, *GetNameSafe(Target));
        SendInputKeyToPlayer(EKeys::E);
        ++InputProofRelicIndex;
    }
    else if (!bFailureProof && Target->IsSafeWindow())
    {
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_STEP Mode=Success Index=%d Relic=%s"), InputProofRelicIndex, *GetNameSafe(Target));
        SendInputKeyToPlayer(EKeys::E);
        ++InputProofRelicIndex;
    }
}

void AFoundryGameMode::SendInputKeyToPlayer(const FKey& Key)
{
    APlayerController* Controller = UGameplayStatics::GetPlayerController(GetWorld(), 0);
    if (!Controller)
    {
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_FAILED Reason=NoPlayerController Key=%s"), *Key.ToString());
        return;
    }

    UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_PROOF_SEND_KEY Key=%s"), *Key.ToString());
    UFoundryRuntimeEvents::Emit(this, TEXT("PLAYER_INPUT"), FString::Printf(TEXT("key=%s route=PlayerControllerInputKey"), *Key.ToString()));
    PRAGMA_DISABLE_DEPRECATION_WARNINGS
    Controller->InputKey(FInputKeyParams(Key, IE_Pressed, 1.0));
    Controller->InputKey(FInputKeyParams(Key, IE_Released, 0.0));
    PRAGMA_ENABLE_DEPRECATION_WARNINGS
}
