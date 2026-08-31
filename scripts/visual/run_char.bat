@echo off
cd /d "C:\Users\11vat\OneDrive\Desktop\11vatedTech-Claude-System
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/visual/character_pipeline.py > "%USERPROFILE%\char_pipeline.log" 2>&1
echo DONE_EXIT=%ERRORLEVEL% >> "%USERPROFILE%\char_pipeline.log"
