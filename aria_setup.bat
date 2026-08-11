@echo off
title Installation Aria Forgedis
color 0B
echo.
echo  ================================================
echo       ARIA FORGEDIS - Installation Windows
echo  ================================================
echo.

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python non detecte. Installation...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_setup.exe'; Start-Process '%TEMP%\python_setup.exe' -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1' -Wait"
)

echo  Installation des composants...
pip install pyautogui --quiet 2>nul
echo  [OK] Composants installes

REM Creer dossier Forgedis
if not exist "%APPDATA%\Forgedis" mkdir "%APPDATA%\Forgedis"

REM Copier agent
copy /Y aria_agent_windows.py "%APPDATA%\Forgedis\aria_agent.py" >nul
echo  [OK] Agent copie

REM Creer script de demarrage VBS (sans fenetre)
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run "python ""%APPDATA%\Forgedis\aria_agent.py""", 0, False
echo WScript.Sleep 2500
echo WshShell.Run """C:\Program Files\Google\Chrome\Application\chrome.exe"" --allow-insecure-localhost --app=""https://aria-forgedis.netlify.app/senior""", 1, False
) > "%APPDATA%\Forgedis\demarrer_aria.vbs"
echo  [OK] Lanceur cree

REM Demarrage automatique Windows
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "AriaForgedis" /t REG_SZ /d "wscript.exe \"%APPDATA%\Forgedis\demarrer_aria.vbs\"" /f >nul
echo  [OK] Demarrage automatique active

REM Raccourci bureau
powershell -Command "$ws=New-Object -ComObject WScript.Shell; $sc=$ws.CreateShortcut('%USERPROFILE%\Desktop\Aria Forgedis.lnk'); $sc.TargetPath='wscript.exe'; $sc.Arguments=chr(34)+'%APPDATA%\Forgedis\demarrer_aria.vbs'+chr(34); $sc.Description='Lancer Aria Forgedis'; $sc.Save()"
echo  [OK] Raccourci bureau cree

echo.
echo  ================================================
echo       Installation terminee !
echo.
echo       Double-cliquez sur "Aria Forgedis"
echo       sur votre bureau pour demarrer.
echo  ================================================
echo.

REM Lancer Aria maintenant
start "" wscript.exe "%APPDATA%\Forgedis\demarrer_aria.vbs"
timeout /t 3 >nul
