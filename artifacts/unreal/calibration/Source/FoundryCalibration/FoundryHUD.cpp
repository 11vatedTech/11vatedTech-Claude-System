#include "FoundryHUD.h"
#include "FoundryGameMode.h"
#include "FoundryGameState.h"
#include "FoundryRelicActor.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

void AFoundryHUD::DrawHUD()
{
    Super::DrawHUD();
    if (FParse::Param(FCommandLine::Get(), TEXT("AshwakeNoHUD"))) return;
    if (!Canvas) return;
    const UFont* Font = GEngine ? GEngine->GetMediumFont() : nullptr;
    Canvas->SetDrawColor(FColor(255, 133, 30));
    Canvas->DrawText(Font, TEXT("ASHWAKE // THE LAST RELIQUARY"), 36.0f, 32.0f, 1.0f, 1.0f, FFontRenderInfo());
    Canvas->SetDrawColor(FColor(200, 210, 200));
    Canvas->DrawText(Font, TEXT("WASD MOVE   MOUSE LOOK   E ATTUNE"), 36.0f, 68.0f, 0.78f, 0.78f, FFontRenderInfo());
    if (AGameModeBase* Mode = GetWorld()->GetAuthGameMode())
    {
        if (UFoundryGameStateComponent* State = Mode->FindComponentByClass<UFoundryGameStateComponent>())
        {
            const FString Status = FString::Printf(TEXT("COALS %d / %d"), State->LitCoals, State->RequiredCoals);
            Canvas->SetDrawColor(FColor(255, 200, 120));
            Canvas->DrawText(Font, *Status, 36.0f, 104.0f, 0.9f, 0.9f, FFontRenderInfo());
            FString StateText;
            switch (State->RunState)
            {
                case EFoundryRunState::Success: StateText = TEXT("RELIQUARY RESTORED"); break;
                case EFoundryRunState::Failure: StateText = TEXT("THE FIRE REJECTED YOU — RESTART"); break;
                default: StateText = TEXT("READ THE PULSE / ATTUNE IN THE GOLD WINDOW"); break;
            }
            Canvas->SetDrawColor(State->RunState == EFoundryRunState::Failure ? FColor(255, 46, 30) : FColor(255, 133, 30));
            Canvas->DrawText(Font, *StateText, 36.0f, 142.0f, 0.82f, 0.82f, FFontRenderInfo());
        }
    }
    Canvas->SetDrawColor(FColor(200, 210, 200));
    Canvas->DrawText(Font, TEXT("A SMALL ORIGINAL GAME-FEEL CALIBRATION"), 36.0f, Canvas->ClipY - 48.0f, 0.62f, 0.62f, FFontRenderInfo());
}
