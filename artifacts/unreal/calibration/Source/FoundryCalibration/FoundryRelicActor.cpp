#include "FoundryRelicActor.h"
#include "FoundryGameState.h"
#include "FoundryGameMode.h"
#include "FoundryRuntimeEvents.h"
#include "Animation/AnimSequence.h"
#include "Engine/AssetManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Sound/SoundWave.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
const TCHAR* RelicPulseStateName(ERelicPulseState State)
{
    switch (State)
    {
        case ERelicPulseState::Reading: return TEXT("Reading");
        case ERelicPulseState::SafeWindow: return TEXT("SafeWindow");
        case ERelicPulseState::Hostile: return TEXT("Hostile");
        case ERelicPulseState::Cooled: return TEXT("Cooled");
        default: return TEXT("Dormant");
    }
}

void LogRuntimeAsset(const TCHAR* Id, const TCHAR* ObjectPath, const TCHAR* ExpectedClass, const UObject* Asset)
{
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASSET_LOADED id=%s object=%s expected_class=%s actual_class=%s loaded=%s"), Id, ObjectPath, ExpectedClass, Asset ? *GetNameSafe(Asset->GetClass()) : TEXT("None"), Asset ? TEXT("true") : TEXT("false"));
    UFoundryRuntimeEvents::Emit(Asset, TEXT("ASSET_LOADED"), FString::Printf(TEXT("id=%s object=%s expected_class=%s actual_class=%s loaded=%s"), Id, ObjectPath, ExpectedClass, Asset ? *GetNameSafe(Asset->GetClass()) : TEXT("None"), Asset ? TEXT("true") : TEXT("false")));
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASSET_RUNTIME_LOADED Id=%s ObjectPath=%s ExpectedClass=%s ActualClass=%s RuntimeLoadable=%d"), Id, ObjectPath, ExpectedClass, Asset ? *GetNameSafe(Asset->GetClass()) : TEXT("None"), Asset ? 1 : 0);
}

void LogAudioPlaying(const TCHAR* Trigger, ERelicPulseState State, const AActor* Actor, const USoundBase* Sound, const UAudioComponent* Audio)
{
    if (Audio && Audio->IsPlaying())
    {
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: AUDIO_PLAYING trigger=%s state=%s actor=%s sound=%s component=%s playing=true"), Trigger, RelicPulseStateName(State), *GetNameSafe(Actor), *GetNameSafe(Sound), *GetNameSafe(Audio));
        UFoundryRuntimeEvents::Emit(Actor, TEXT("AUDIO_PLAYING"), FString::Printf(TEXT("trigger=%s state=%s actor=%s sound=%s component=%s playing=true"), Trigger, RelicPulseStateName(State), *GetNameSafe(Actor), *GetNameSafe(Sound), *GetNameSafe(Audio)));
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("LogFoundry: AUDIO_NOT_PLAYING trigger=%s state=%s actor=%s sound=%s component=%s playing=false"), Trigger, RelicPulseStateName(State), *GetNameSafe(Actor), *GetNameSafe(Sound), *GetNameSafe(Audio));
    }
}
}

AFoundryRelicActor::AFoundryRelicActor()
{
    PrimaryActorTick.bCanEverTick = true;
    RelicMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("EmberveilRelic"));
    RootComponent = RelicMesh;
    AttuneVFX = CreateDefaultSubobject<UNiagaraComponent>(TEXT("AttuneVFX"));
    AttuneVFX->SetupAttachment(RootComponent);
    AttuneVFX->SetAutoActivate(true);
    StateLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("StateLight"));
    StateLight->SetupAttachment(RootComponent);
    StateLight->Intensity = 1800.0f;
    StateLight->AttenuationRadius = 360.0f;
    RelicMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> MeshFinder(TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/glass_bell.glass_bell"));
    if (MeshFinder.Succeeded())
    {
        RelicMesh->SetSkeletalMesh(MeshFinder.Object);
    }
    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> VFXFinder(TEXT("/Game/Calibration/VFX/NS_Emberveil_Attune.NS_Emberveil_Attune"));
    if (VFXFinder.Succeeded())
    {
        AttuneVFXSystem = VFXFinder.Object;
        AttuneVFX->SetAsset(AttuneVFXSystem);
    }
    static ConstructorHelpers::FObjectFinder<USoundBase> SafeSoundFinder(TEXT("/Game/Calibration/Audio/S_Ashwake_SafeWindow.S_Ashwake_SafeWindow"));
    static ConstructorHelpers::FObjectFinder<USoundBase> HostileSoundFinder(TEXT("/Game/Calibration/Audio/S_Ashwake_Hostile.S_Ashwake_Hostile"));
    static ConstructorHelpers::FObjectFinder<USoundBase> SuccessSoundFinder(TEXT("/Game/Calibration/Audio/S_Ashwake_AttuneSuccess.S_Ashwake_AttuneSuccess"));
    static ConstructorHelpers::FObjectFinder<USoundBase> RejectSoundFinder(TEXT("/Game/Calibration/Audio/S_Ashwake_AttuneReject.S_Ashwake_AttuneReject"));
    if (SafeSoundFinder.Succeeded()) SafeWindowSound = SafeSoundFinder.Object;
    if (HostileSoundFinder.Succeeded()) HostileSound = HostileSoundFinder.Object;
    if (SuccessSoundFinder.Succeeded()) SuccessSound = SuccessSoundFinder.Object;
    if (RejectSoundFinder.Succeeded()) RejectSound = RejectSoundFinder.Object;
    static ConstructorHelpers::FObjectFinder<UAnimationAsset> ReadingAnimFinder(TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_float_Emberveil_root.emberveil-canonical11vt_float_Emberveil_root"));
    static ConstructorHelpers::FObjectFinder<UAnimationAsset> SafeAnimFinder(TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_rotate_brass_band.emberveil-canonical11vt_rotate_brass_band"));
    static ConstructorHelpers::FObjectFinder<UAnimationAsset> HostileAnimFinder(TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_pulse_ember_core.emberveil-canonical11vt_pulse_ember_core"));
    static ConstructorHelpers::FObjectFinder<UAnimationAsset> SuccessAnimFinder(TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_rotate_filigree_arc.emberveil-canonical11vt_rotate_filigree_arc"));
    if (ReadingAnimFinder.Succeeded()) ReadingAnimation = ReadingAnimFinder.Object;
    if (SafeAnimFinder.Succeeded()) SafeWindowAnimation = SafeAnimFinder.Object;
    if (HostileAnimFinder.Succeeded()) HostileAnimation = HostileAnimFinder.Object;
    if (SuccessAnimFinder.Succeeded()) SuccessAnimation = SuccessAnimFinder.Object;
}

void AFoundryRelicActor::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: RELIQUARY_BEGINPLAY Actor=%s"), *GetNameSafe(this));
    for (int32 Index = 0; Index < RelicMesh->GetNumMaterials(); ++Index)
    {
        if (UMaterialInstanceDynamic* Material = RelicMesh->CreateAndSetMaterialInstanceDynamic(Index))
        {
            DynamicMaterials.Add(Material);
        }
    }
    FeedbackSound = SuccessSound;
    LogRuntimeAsset(TEXT("emberveil_attune_vfx"), TEXT("/Game/Calibration/VFX/NS_Emberveil_Attune.NS_Emberveil_Attune"), TEXT("NiagaraSystem"), AttuneVFXSystem);
    LogRuntimeAsset(TEXT("ashwake_safe_window_audio"), TEXT("/Game/Calibration/Audio/S_Ashwake_SafeWindow.S_Ashwake_SafeWindow"), TEXT("SoundWave"), SafeWindowSound);
    LogRuntimeAsset(TEXT("ashwake_hostile_audio"), TEXT("/Game/Calibration/Audio/S_Ashwake_Hostile.S_Ashwake_Hostile"), TEXT("SoundWave"), HostileSound);
    LogRuntimeAsset(TEXT("ashwake_attune_success_audio"), TEXT("/Game/Calibration/Audio/S_Ashwake_AttuneSuccess.S_Ashwake_AttuneSuccess"), TEXT("SoundWave"), SuccessSound);
    LogRuntimeAsset(TEXT("ashwake_attune_reject_audio"), TEXT("/Game/Calibration/Audio/S_Ashwake_AttuneReject.S_Ashwake_AttuneReject"), TEXT("SoundWave"), RejectSound);
    LogRuntimeAsset(TEXT("emberveil_idle_animation"), TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_float_Emberveil_root.emberveil-canonical11vt_float_Emberveil_root"), TEXT("AnimSequence"), ReadingAnimation);
    LogRuntimeAsset(TEXT("emberveil_safe_animation"), TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_rotate_brass_band.emberveil-canonical11vt_rotate_brass_band"), TEXT("AnimSequence"), SafeWindowAnimation);
    LogRuntimeAsset(TEXT("emberveil_hostile_animation"), TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_pulse_ember_core.emberveil-canonical11vt_pulse_ember_core"), TEXT("AnimSequence"), HostileAnimation);
    LogRuntimeAsset(TEXT("emberveil_success_animation"), TEXT("/Game/Calibration/Emberveil/emberveil-canonical/SkeletalMeshes/emberveil-canonical11vt_rotate_filigree_arc.emberveil-canonical11vt_rotate_filigree_arc"), TEXT("AnimSequence"), SuccessAnimation);
    SetPulseState(ERelicPulseState::Reading);
}

void AFoundryRelicActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    StateTime += DeltaSeconds;
    PulsePhase += DeltaSeconds;
    const float Pulse = 0.5f + 0.5f * FMath::Sin(PulsePhase * 2.8f);
    if (AttuneVFX) AttuneVFX->SetVariableFloat(TEXT("User.Pulse"), Pulse);
    for (UMaterialInstanceDynamic* Material : DynamicMaterials)
    {
        if (Material)
        {
            Material->SetScalarParameterValue(TEXT("Pulse"), Pulse);
            Material->SetScalarParameterValue(TEXT("EmberIntensity"), PulseState == ERelicPulseState::Hostile ? 7.0f : 2.0f + Pulse * 2.0f);
        }
    }
    if (PulseState == ERelicPulseState::Reading && StateTime > 2.0f) SetPulseState(ERelicPulseState::SafeWindow);
    else if (PulseState == ERelicPulseState::SafeWindow && StateTime > 3.0f) SetPulseState(ERelicPulseState::Hostile);
    else if (PulseState == ERelicPulseState::Hostile && StateTime > 1.5f) SetPulseState(ERelicPulseState::Reading);
}

bool AFoundryRelicActor::TryAttune()
{
    if (PulseState != ERelicPulseState::SafeWindow)
    {
        if (UFoundryGameStateComponent* State = FindComponentByClass<UFoundryGameStateComponent>()) State->FailRun();
        if (AGameModeBase* Mode = GetWorld()->GetAuthGameMode())
        {
            if (UFoundryGameStateComponent* GameState = Mode->FindComponentByClass<UFoundryGameStateComponent>()) GameState->FailRun();
        }
        if (RejectSound)
        {
            UAudioComponent* RejectAudio = UGameplayStatics::SpawnSoundAtLocation(this, RejectSound, GetActorLocation(), FRotator::ZeroRotator, 0.45f);
            LogAudioPlaying(TEXT("InteractionRejected"), PulseState, this, RejectSound, RejectAudio);
        }
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INTERACTION_REJECTED actor=%s state=%s rule=RequiresSafeWindow accepted=false"), *GetNameSafe(this), RelicPulseStateName(PulseState));
        UFoundryRuntimeEvents::Emit(this, TEXT("INTERACTION_REJECTED"), FString::Printf(TEXT("actor=%s state=%s rule=RequiresSafeWindow accepted=false"), *GetNameSafe(this), RelicPulseStateName(PulseState)));
        SetPulseState(ERelicPulseState::Hostile);
        return false;
    }
    bool bSuccess = false;
    if (AGameModeBase* Mode = GetWorld()->GetAuthGameMode())
    {
        if (UFoundryGameStateComponent* GameState = Mode->FindComponentByClass<UFoundryGameStateComponent>()) bSuccess = GameState->RegisterAttunement(true);
    }
    if (bSuccess)
    {
        if (SuccessSound)
        {
            UAudioComponent* SuccessAudio = UGameplayStatics::SpawnSoundAtLocation(this, SuccessSound, GetActorLocation(), FRotator::ZeroRotator, 0.75f);
            LogAudioPlaying(TEXT("InteractionAccepted"), PulseState, this, SuccessSound, SuccessAudio);
        }
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INTERACTION_ACCEPTED actor=%s state=%s rule=SafeWindow accepted=true"), *GetNameSafe(this), RelicPulseStateName(PulseState));
        UFoundryRuntimeEvents::Emit(this, TEXT("INTERACTION_ACCEPTED"), FString::Printf(TEXT("actor=%s state=%s rule=SafeWindow accepted=true"), *GetNameSafe(this), RelicPulseStateName(PulseState)));
        SetPulseState(ERelicPulseState::Cooled);
    }
    return bSuccess;
}

void AFoundryRelicActor::SetPulseState(ERelicPulseState NewState)
{
    PulseState = NewState;
    StateTime = 0.0f;
    ApplyStatePresentation(NewState);
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: RELIQUARY_STATE Actor=%s State=%d"), *GetNameSafe(this), static_cast<int32>(NewState));
}

void AFoundryRelicActor::ForceEvidenceState(ERelicPulseState NewState)
{
    SetPulseState(NewState);
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: ASHWAKE_PHASE3_FORCED_RELIQUARY_STATE Actor=%s State=%s"), *GetNameSafe(this), RelicPulseStateName(NewState));
    UFoundryRuntimeEvents::Emit(this, TEXT("PHASE3_FORCED_RELIQUARY_STATE"), FString::Printf(TEXT("actor=%s state=%s"), *GetNameSafe(this), RelicPulseStateName(NewState)));
}

void AFoundryRelicActor::ApplyStatePresentation(ERelicPulseState NewState)
{
    const FLinearColor StateColor = NewState == ERelicPulseState::SafeWindow ? FLinearColor(1.0f, 0.64f, 0.18f) :
        NewState == ERelicPulseState::Hostile ? FLinearColor(1.0f, 0.05f, 0.02f) :
        NewState == ERelicPulseState::Cooled ? FLinearColor(0.18f, 0.74f, 1.0f) : FLinearColor(0.35f, 0.12f, 0.04f);
    const float SpawnRate = NewState == ERelicPulseState::SafeWindow ? 48.0f : NewState == ERelicPulseState::Hostile ? 96.0f : NewState == ERelicPulseState::Cooled ? 18.0f : 24.0f;
    const float Energy = NewState == ERelicPulseState::Hostile ? 1.0f : NewState == ERelicPulseState::SafeWindow ? 0.72f : NewState == ERelicPulseState::Cooled ? 0.38f : 0.45f;
    if (AttuneVFX)
    {
        AttuneVFX->SetVariableLinearColor(TEXT("User.StateColor"), StateColor);
        AttuneVFX->SetVariableFloat(TEXT("User.SpawnRate"), SpawnRate);
        AttuneVFX->SetVariableFloat(TEXT("User.Energy"), Energy);
        AttuneVFX->SetVariableFloat(TEXT("User.State"), static_cast<float>(NewState));
        AttuneVFX->Activate(true);
    }
    const bool bVFXActive = AttuneVFX && AttuneVFXSystem;
    if (StateLight)
    {
        StateLight->SetLightColor(StateColor);
        StateLight->SetIntensity(NewState == ERelicPulseState::Hostile ? 4200.0f : NewState == ERelicPulseState::SafeWindow ? 3000.0f : NewState == ERelicPulseState::Cooled ? 2200.0f : 1200.0f);
        StateLight->SetAttenuationRadius(NewState == ERelicPulseState::Hostile ? 520.0f : 360.0f);
    }
    if (UAnimationAsset* Animation = AnimationForState(NewState))
    {
        RelicMesh->PlayAnimation(Animation, NewState != ERelicPulseState::Cooled);
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: ANIMATION_PLAYING clip=%s target=%s state=%s playing=%s looping=%s"), *GetNameSafe(Animation), *GetNameSafe(RelicMesh), RelicPulseStateName(NewState), RelicMesh->IsPlaying() ? TEXT("true") : TEXT("false"), NewState != ERelicPulseState::Cooled ? TEXT("true") : TEXT("false"));
        UFoundryRuntimeEvents::Emit(this, TEXT("ANIMATION_PLAYING"), FString::Printf(TEXT("clip=%s target=%s state=%s playing=%s looping=%s"), *GetNameSafe(Animation), *GetNameSafe(RelicMesh), RelicPulseStateName(NewState), RelicMesh->IsPlaying() ? TEXT("true") : TEXT("false"), NewState != ERelicPulseState::Cooled ? TEXT("true") : TEXT("false")));
    }
    if (USoundBase* StateSound = SoundForState(NewState))
    {
        UAudioComponent* StateAudio = UGameplayStatics::SpawnSoundAtLocation(this, StateSound, GetActorLocation(), FRotator::ZeroRotator, NewState == ERelicPulseState::Hostile ? 0.65f : 0.5f);
        LogAudioPlaying(TEXT("StateChange"), NewState, this, StateSound, StateAudio);
    }
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: VFX_STATE system=%s state=%s component=%s active=%s spawn_rate=%.1f energy=%.2f color=(%.2f,%.2f,%.2f,%.2f)"), *GetNameSafe(AttuneVFXSystem), RelicPulseStateName(NewState), *GetNameSafe(AttuneVFX), bVFXActive ? TEXT("true") : TEXT("false"), SpawnRate, Energy, StateColor.R, StateColor.G, StateColor.B, StateColor.A);
    UFoundryRuntimeEvents::Emit(this, TEXT("VFX_STATE"), FString::Printf(TEXT("system=%s state=%s component=%s active=%s spawn_rate=%.1f energy=%.2f color=(%.2f,%.2f,%.2f,%.2f)"), *GetNameSafe(AttuneVFXSystem), RelicPulseStateName(NewState), *GetNameSafe(AttuneVFX), bVFXActive ? TEXT("true") : TEXT("false"), SpawnRate, Energy, StateColor.R, StateColor.G, StateColor.B, StateColor.A));
}

UAnimationAsset* AFoundryRelicActor::AnimationForState(ERelicPulseState State) const
{
    switch (State)
    {
        case ERelicPulseState::SafeWindow: return SafeWindowAnimation ? SafeWindowAnimation.Get() : ReadingAnimation.Get();
        case ERelicPulseState::Hostile: return HostileAnimation ? HostileAnimation.Get() : ReadingAnimation.Get();
        case ERelicPulseState::Cooled: return SuccessAnimation ? SuccessAnimation.Get() : ReadingAnimation.Get();
        default: return ReadingAnimation.Get();
    }
}

USoundBase* AFoundryRelicActor::SoundForState(ERelicPulseState State) const
{
    switch (State)
    {
        case ERelicPulseState::SafeWindow: return SafeWindowSound.Get();
        case ERelicPulseState::Hostile: return HostileSound.Get();
        default: return nullptr;
    }
}
