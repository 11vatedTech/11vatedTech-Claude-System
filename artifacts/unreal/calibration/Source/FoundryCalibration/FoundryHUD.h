#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "FoundryHUD.generated.h"

UCLASS()
class FOUNDRYCALIBRATION_API AFoundryHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};
