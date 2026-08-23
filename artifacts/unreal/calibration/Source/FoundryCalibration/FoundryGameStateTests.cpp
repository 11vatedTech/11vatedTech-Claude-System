#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "FoundryGameState.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFoundryGameStateTransitions, "FoundryCalibration.Gameplay.GameStateTransitions", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FFoundryGameStateTransitions::RunTest(const FString& Parameters)
{
    UFoundryGameStateComponent* State = NewObject<UFoundryGameStateComponent>();
    State->RequiredCoals = 1;
    State->BeginRun();
    TestEqual(TEXT("BeginRun enters Playing"), State->RunState, EFoundryRunState::Playing);
    TestFalse(TEXT("Unsafe attunement fails the run"), State->RegisterAttunement(false));
    TestEqual(TEXT("Unsafe attunement enters Failure"), State->RunState, EFoundryRunState::Failure);
    State->RestartRun();
    TestEqual(TEXT("Restart returns to Playing"), State->RunState, EFoundryRunState::Playing);
    TestTrue(TEXT("Safe attunement succeeds"), State->RegisterAttunement(true));
    TestEqual(TEXT("Required coal enters Success"), State->RunState, EFoundryRunState::Success);
    TestFalse(TEXT("Success cannot be mutated by a second attunement"), State->RegisterAttunement(true));
    return true;
}
#endif
