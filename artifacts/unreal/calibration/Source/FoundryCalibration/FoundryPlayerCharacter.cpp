#include "FoundryPlayerCharacter.h"
#include "FoundryRelicActor.h"
#include "FoundryGameState.h"
#include "FoundryRuntimeEvents.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputActionValue.h"
#include "Engine/LocalPlayer.h"
#include "EngineUtils.h"
#include "GameFramework/GameModeBase.h"

AFoundryPlayerCharacter::AFoundryPlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->MaxWalkSpeed = 420.0f;
    GetCharacterMovement()->MaxAcceleration = 1800.0f;
    GetCharacterMovement()->BrakingDecelerationWalking = 1500.0f;

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 520.0f;
    CameraBoom->SetRelativeRotation(FRotator(-18.0f, 0.0f, 0.0f));
    CameraBoom->bUsePawnControlRotation = true;

    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    FollowCamera->bUsePawnControlRotation = false;

    MappingContext = NewObject<UInputMappingContext>(this, TEXT("FoundryMappingContext"));
    MoveAction = NewObject<UInputAction>(this, TEXT("MoveAction"));
    MoveAction->ValueType = EInputActionValueType::Axis2D;
    LookAction = NewObject<UInputAction>(this, TEXT("LookAction"));
    LookAction->ValueType = EInputActionValueType::Axis2D;
    AttuneAction = NewObject<UInputAction>(this, TEXT("AttuneAction"));
    AttuneAction->ValueType = EInputActionValueType::Boolean;
    RestartAction = NewObject<UInputAction>(this, TEXT("RestartAction"));
    RestartAction->ValueType = EInputActionValueType::Boolean;
    MappingContext->MapKey(MoveAction, EKeys::W);
    MappingContext->MapKey(MoveAction, EKeys::S);
    MappingContext->MapKey(MoveAction, EKeys::A);
    MappingContext->MapKey(MoveAction, EKeys::D);
    MappingContext->MapKey(LookAction, EKeys::MouseX);
    MappingContext->MapKey(LookAction, EKeys::MouseY);
    MappingContext->MapKey(AttuneAction, EKeys::E);
    MappingContext->MapKey(RestartAction, EKeys::R);
}

void AFoundryPlayerCharacter::BeginPlay()
{
    Super::BeginPlay();
    if (APlayerController* PlayerController = Cast<APlayerController>(GetController()))
    {
        if (ULocalPlayer* LocalPlayer = PlayerController->GetLocalPlayer())
        {
            if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>()) Subsystem->AddMappingContext(MappingContext, 0);
        }
    }
}

void AFoundryPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    if (UEnhancedInputComponent* Enhanced = Cast<UEnhancedInputComponent>(PlayerInputComponent))
    {
        Enhanced->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AFoundryPlayerCharacter::Move);
        Enhanced->BindAction(LookAction, ETriggerEvent::Triggered, this, &AFoundryPlayerCharacter::Look);
        Enhanced->BindAction(AttuneAction, ETriggerEvent::Started, this, &AFoundryPlayerCharacter::Attune);
        Enhanced->BindAction(RestartAction, ETriggerEvent::Started, this, &AFoundryPlayerCharacter::Restart);
    }
}

void AFoundryPlayerCharacter::Move(const FInputActionValue& Value)
{
    const FVector2D Movement = Value.Get<FVector2D>();
    if (Controller)
    {
        const FRotator Rotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
        AddMovementInput(FRotationMatrix(Rotation).GetUnitAxis(EAxis::X), Movement.Y);
        AddMovementInput(FRotationMatrix(Rotation).GetUnitAxis(EAxis::Y), Movement.X);
    }
}

void AFoundryPlayerCharacter::Look(const FInputActionValue& Value)
{
    const FVector2D LookAxis = Value.Get<FVector2D>();
    AddControllerYawInput(LookAxis.X * 0.8f);
    AddControllerPitchInput(LookAxis.Y * -0.8f);
}

void AFoundryPlayerCharacter::Attune()
{
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_RECEIVED action=Attune pawn=%s route=EnhancedInput"), *GetNameSafe(this));
    UFoundryRuntimeEvents::Emit(this, TEXT("INPUT_ACTION_TRIGGERED"), FString::Printf(TEXT("action=Attune pawn=%s route=EnhancedInput"), *GetNameSafe(this)));
    AFoundryRelicActor* Closest = nullptr;
    float ClosestDistance = 350.0f;
    for (TActorIterator<AFoundryRelicActor> It(GetWorld()); It; ++It)
    {
        const float Distance = FVector::Dist(GetActorLocation(), It->GetActorLocation());
        if (Distance < ClosestDistance)
        {
            Closest = *It;
            ClosestDistance = Distance;
        }
    }
    if (!Closest)
    {
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INTERACTION_QUERY pawn=%s result=NoRelicInRange radius=350.0 route=EnhancedInput"), *GetNameSafe(this));
        UFoundryRuntimeEvents::Emit(this, TEXT("INTERACTION_QUERY"), FString::Printf(TEXT("pawn=%s result=NoRelicInRange radius=350.0 route=EnhancedInput"), *GetNameSafe(this)));
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: INTERACTION_REJECTED reason=NoRelicInRange pawn=%s accepted=false"), *GetNameSafe(this));
        UFoundryRuntimeEvents::Emit(this, TEXT("INTERACTION_REJECTED"), FString::Printf(TEXT("reason=NoRelicInRange pawn=%s accepted=false"), *GetNameSafe(this)));
        return;
    }
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: INTERACTION_QUERY pawn=%s target=%s distance=%.1f safe_window=%s route=EnhancedInput"), *GetNameSafe(this), *GetNameSafe(Closest), ClosestDistance, Closest->IsSafeWindow() ? TEXT("true") : TEXT("false"));
    UFoundryRuntimeEvents::Emit(this, TEXT("INTERACTION_QUERY"), FString::Printf(TEXT("pawn=%s target=%s distance=%.1f safe_window=%s route=EnhancedInput"), *GetNameSafe(this), *GetNameSafe(Closest), ClosestDistance, Closest->IsSafeWindow() ? TEXT("true") : TEXT("false")));
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: GAMEPLAY_COMMAND action=Attune target=%s distance=%.1f rule=SafeWindowRequired"), *GetNameSafe(Closest), ClosestDistance);
    UFoundryRuntimeEvents::Emit(this, TEXT("GAMEPLAY_RULE"), FString::Printf(TEXT("action=Attune target=%s distance=%.1f rule=SafeWindowRequired safe_window=%s"), *GetNameSafe(Closest), ClosestDistance, Closest->IsSafeWindow() ? TEXT("true") : TEXT("false")));
    const bool bAccepted = Closest->TryAttune();
    if (AGameModeBase* Mode = GetWorld()->GetAuthGameMode())
    {
        if (UFoundryGameStateComponent* State = Mode->FindComponentByClass<UFoundryGameStateComponent>())
        {
            if (State->RunState == EFoundryRunState::Success)
            {
                UE_LOG(LogTemp, Display, TEXT("LogFoundry: SUCCESS lit_coals=%d required_coals=%d"), State->LitCoals, State->RequiredCoals);
                UE_LOG(LogTemp, Display, TEXT("LogFoundry: PLAYER_SUCCESS LitCoals=%d RequiredCoals=%d"), State->LitCoals, State->RequiredCoals);
                UFoundryRuntimeEvents::Emit(this, TEXT("SUCCESS"), FString::Printf(TEXT("lit_coals=%d required_coals=%d"), State->LitCoals, State->RequiredCoals));
            }
            else if (State->RunState == EFoundryRunState::Failure)
            {
                UE_LOG(LogTemp, Display, TEXT("LogFoundry: FAILURE lit_coals=%d required_coals=%d"), State->LitCoals, State->RequiredCoals);
                UE_LOG(LogTemp, Display, TEXT("LogFoundry: PLAYER_FAILURE LitCoals=%d RequiredCoals=%d"), State->LitCoals, State->RequiredCoals);
                UFoundryRuntimeEvents::Emit(this, TEXT("FAILURE"), FString::Printf(TEXT("lit_coals=%d required_coals=%d"), State->LitCoals, State->RequiredCoals));
            }
            else
            {
                UE_LOG(LogTemp, Display, TEXT("LogFoundry: PLAYER_PROGRESS Accepted=%d LitCoals=%d RequiredCoals=%d"), bAccepted ? 1 : 0, State->LitCoals, State->RequiredCoals);
            }
        }
    }
}

void AFoundryPlayerCharacter::Restart()
{
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: INPUT_RECEIVED action=Restart pawn=%s route=EnhancedInput"), *GetNameSafe(this));
    UFoundryRuntimeEvents::Emit(this, TEXT("INPUT_ACTION_TRIGGERED"), FString::Printf(TEXT("action=Restart pawn=%s route=EnhancedInput"), *GetNameSafe(this)));
    if (AGameModeBase* Mode = GetWorld()->GetAuthGameMode())
    {
        if (UFoundryGameStateComponent* State = Mode->FindComponentByClass<UFoundryGameStateComponent>())
        {
            State->RestartRun();
            UE_LOG(LogTemp, Display, TEXT("LogFoundry: RESTART run_state=%d lit_coals=%d playable=true"), static_cast<int32>(State->RunState), State->LitCoals);
            UE_LOG(LogTemp, Display, TEXT("LogFoundry: RECOVERY_RESTART RunState=%d LitCoals=%d"), static_cast<int32>(State->RunState), State->LitCoals);
            UFoundryRuntimeEvents::Emit(this, TEXT("RESTART"), FString::Printf(TEXT("run_state=%d lit_coals=%d playable=true"), static_cast<int32>(State->RunState), State->LitCoals));
        }
    }
}
