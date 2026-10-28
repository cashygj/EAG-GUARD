@echo off
REM Double-click this file (or run it from a terminal) to execute run_all.ps1.
REM It bypasses the PowerShell execution policy for this one invocation.
REM
REM   run_all.cmd                 run everything (slices + full domains, both arms)
REM   run_all.cmd -Scope slice    slices only
REM   run_all.cmd -Domains slack  slack only
REM   run_all.cmd -Status         show progress, run nothing
REM
REM You can press Ctrl+C at any time. Running it again resumes from where it
REM stopped; finished pairs are never re-run.

setlocal
set "PS=pwsh"
where pwsh >nul 2>nul || set "PS=powershell"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_all.ps1" %*
exit /b %ERRORLEVEL%
