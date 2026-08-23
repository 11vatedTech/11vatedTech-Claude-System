# Unreal Game Studio — Initial Platform Research

Date: 2026-08-19

## Machine evidence

- Installed engine root: `C:/Program Files/Epic Games/UE_5.8`
- Installed build: `5.8.0`, changelist `55116800`, branch `++UE5+Release-5.8`
- `UnrealEditor.exe`, `UnrealEditor-Cmd.exe`, `RunUAT.bat`, and `Build.bat` are present.
- Windows 10 SDK root is present.
- `dotnet` is present; `cl` and `msbuild` are not discoverable from the current shell, so C++ build readiness is not claimed.
- Relevant installed plugin families include PythonScriptPlugin, RemoteControl, DataValidation, Niagara, PCG, Control Rig, Enhanced Input, and GameplayAbilities. Presence is not equivalent to project enablement or runtime proof.
- Existing projects discovered: `Nemesis` (EngineAssociation 5.6, C++ module, 2 maps) and `MyProject` (EngineAssociation GUID, no declared module in the project descriptor).

## Official Epic evidence

Epic's Unreal Engine 5.8 Data Validation documentation states that the Data Validation plugin validates individual assets, dependencies, folders, or a project; it exposes command-line validation through:

```text
UnrealEditor-Cmd.exe <PROJECT_NAME>.uproject -run=DataValidation
```

The same documentation describes `UEditorValidatorBase` and `IsDataValid`/`ValidateLoadedAsset` as native extension points, and notes that Python validators must register with `UEditorValidatorSubsystem`. Source: <https://dev.epicgames.com/documentation/en-us/unreal-engine/data-validation-in-unreal-engine>

## Foundry decisions

1. Static `.uproject`/content inspection is a separate capability from launching an editor.
2. Editor Python, commandlets, UAT, and Remote Control will be selected per operation; GUI clicking is not the primary boundary.
3. The first executable slice is health + semantic project inspection + governed Blender handoff. A bounded `DataValidation` commandlet runner was then exercised successfully against the minimal Unreal 5.8 calibration project; the same commandlet recorded a real plugin-load failure against the existing MyProject, so both success and failure evidence are preserved. The structured Editor-Python/AssetTools operation then imported the canonical Emberveil GLB into `/Game/Calibration/Emberveil`, producing 25 imported object paths and real `.uasset` files. Packaged play remains unclaimed.
4. Unreal content validation must preserve provenance and import-contract data. A valid GLB or successful commandlet is not evidence of game design, game feel, or visual quality.
