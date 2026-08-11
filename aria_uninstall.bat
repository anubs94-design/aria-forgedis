@echo off
title Desinstallation Aria Forgedis
echo Desinstallation d'Aria Forgedis...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "AriaForgedis" /f >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Aria*" >nul 2>&1
rmdir /S /Q "%APPDATA%\Forgedis" >nul 2>&1
del "%USERPROFILE%\Desktop\Aria Forgedis.lnk" >nul 2>&1
echo Aria Forgedis a ete desinstalle.
pause
