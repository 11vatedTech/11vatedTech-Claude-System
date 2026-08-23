using UnrealBuildTool;

public class FoundryCalibration : ModuleRules
{
    public FoundryCalibration(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "Niagara"
        });
    }
}
