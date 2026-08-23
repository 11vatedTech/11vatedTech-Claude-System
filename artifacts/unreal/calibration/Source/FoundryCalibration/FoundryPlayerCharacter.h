#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "FoundryPlayerCharacter.generated.h"

class UInputAction;
class UInputMappingContext;

UCLASS()
class FOUNDRYCALIBRATION_API AFoundryPlayerCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    AFoundryPlayerCharacter();
    virtual void BeginPlay() override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Foundry|Camera")
    TObjectPtr<class USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Foundry|Camera")
    TObjectPtr<class UCameraComponent> FollowCamera;

    UPROPERTY()
    TObjectPtr<UInputMappingContext> MappingContext;

    UPROPERTY()
    TObjectPtr<UInputAction> MoveAction;

    UPROPERTY()
    TObjectPtr<UInputAction> LookAction;

    UPROPERTY()
    TObjectPtr<UInputAction> AttuneAction;

    UPROPERTY()
    TObjectPtr<UInputAction> RestartAction;

private:
    void Move(const struct FInputActionValue& Value);
    void Look(const struct FInputActionValue& Value);
    void Attune();
    void Restart();
};
