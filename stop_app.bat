@echo off
cd /d %~dp0
:: Set console code page to UTF-8 so accented characters print correctly
chcp 65001 > nul
set ARG=
set KILLPID=
:: map supported switches: /f -> -Force, /l -> -List, /h -> -Help, /k <pid> -> -Kill <pid>
if /I "%1"=="/f" set ARG=%ARG% -Force
if /I "%2"=="/f" set ARG=%ARG% -Force
if /I "%3"=="/f" set ARG=%ARG% -Force
if /I "%1"=="/l" set ARG=%ARG% -List
if /I "%2"=="/l" set ARG=%ARG% -List
if /I "%3"=="/l" set ARG=%ARG% -List
if /I "%1"=="/h" set ARG=%ARG% -Help
if /I "%2"=="/h" set ARG=%ARG% -Help
if /I "%3"=="/h" set ARG=%ARG% -Help
if /I "%1"=="/k" set KILLPID=%2
if /I "%2"=="/k" set KILLPID=%3
if /I "%3"=="/k" set KILLPID=%4
if defined KILLPID set ARG=%ARG% -Kill %KILLPID%
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_app.ps1" %ARG%
