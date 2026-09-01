@echo off
title Render Full Deploy - Card Ready
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\card-ready-deploy.ps1"
pause
