@echo off
cd /d "C:\Users\11vat\OneDrive\Desktop\11vatedTech-Claude-System"
set PATH=C:\Users\11vat\.acestep-venv\Scripts;%PATH%
C:\Users\11vat\.acestep-venv\Scripts\python.exe scripts/visual/wan_diffusers_gen.py > "%USERPROFILE%\wan_diffusers_py312.log" 2>&1
echo DONE_EXIT=%ERRORLEVEL% >> "%USERPROFILE%\wan_diffusers_py312.log"
