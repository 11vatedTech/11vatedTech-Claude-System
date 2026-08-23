#include "FoundryGameState.h"
#include "FoundryRuntimeEvents.h"

namespace
{
const TCHAR* RunStateName(EFoundryRunState State)
{
    switch (State)
    {
        case EFoundryRunState::Start: return TEXT("Start");
        case EFoundryRunState::Playing: return TEXT("Playing");
        case EFoundryRunState::Success: return TEXT("Success");
        case EFoundryRunState::Failure: return TEXT("Failure");
        case EFoundryRunState::Restart: return TEXT("Restart");
        default: return TEXT("Unknown");
    }
}
}

UFoundryGameStateComponent::UFoundryGameStateComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UFoundryGameStateComponent::BeginRun()
{
    if (RunState == EFoundryRunState::Start || RunState == EFoundryRunState::Restart)
    {
        RunState = EFoundryRunState::Playing;
        LitCoals = 0;
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: STATE_CHANGED run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals);
        UFoundryRuntimeEvents::Emit(this, TEXT("STATE_CONSEQUENCE"), FString::Printf(TEXT("run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals));
    }
}

bool UFoundryGameStateComponent::RegisterAttunement(bool bSafeWindow)
{
    if (RunState != EFoundryRunState::Playing || !bSafeWindow)
    {
        if (RunState == EFoundryRunState::Playing && !bSafeWindow)
        {
            FailRun();
        }
        return false;
    }
    LitCoals = FMath::Clamp(LitCoals + 1, 0, RequiredCoals);
    UE_LOG(LogTemp, Display, TEXT("LogFoundry: STATE_CHANGED run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals);
    UFoundryRuntimeEvents::Emit(this, TEXT("STATE_CONSEQUENCE"), FString::Printf(TEXT("run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals));
    if (LitCoals >= RequiredCoals)
    {
        RunState = EFoundryRunState::Success;
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: STATE_CHANGED run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals);
        UFoundryRuntimeEvents::Emit(this, TEXT("STATE_CONSEQUENCE"), FString::Printf(TEXT("run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals));
    }
    return true;
}

void UFoundryGameStateComponent::FailRun()
{
    if (RunState == EFoundryRunState::Playing)
    {
        RunState = EFoundryRunState::Failure;
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: STATE_CHANGED run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals);
        UFoundryRuntimeEvents::Emit(this, TEXT("STATE_CONSEQUENCE"), FString::Printf(TEXT("run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals));
    }
}

void UFoundryGameStateComponent::RestartRun()
{
    if (RunState == EFoundryRunState::Failure || RunState == EFoundryRunState::Success)
    {
        RunState = EFoundryRunState::Restart;
        UE_LOG(LogTemp, Display, TEXT("LogFoundry: STATE_CHANGED run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals);
        UFoundryRuntimeEvents::Emit(this, TEXT("STATE_CONSEQUENCE"), FString::Printf(TEXT("run_state=%s run_state_value=%d lit_coals=%d required_coals=%d"), RunStateName(RunState), static_cast<int32>(RunState), LitCoals, RequiredCoals));
        BeginRun();
    }
}
