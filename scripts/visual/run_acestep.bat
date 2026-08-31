@echo off
cd /d "C:\Users\11vat\OneDrive\Desktop\11vatedTech-Claude-System"
python scripts/visual/acestep_generate.py > "%USERPROFILE%\acestep_gen.log" 2>&1
echo DONE_EXIT=%ERRORLEVEL% >> "%USERPROFILE%\acestep_gen.log"
