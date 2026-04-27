@echo off
CHCP 65001 > nul

set PROJECT_ROOT=%~dp0..
pushd "%PROJECT_ROOT%"
set PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%

set DATASET_NAME=%1
if "%DATASET_NAME%"=="" set DATASET_NAME=ALL

set PYTHON_EXE=%COMP396_PYTHON%
if "%PYTHON_EXE%"=="" if exist "D:\Anacoda\envs\comp396\python.exe" set PYTHON_EXE=D:\Anacoda\envs\comp396\python.exe
if "%PYTHON_EXE%"=="" set PYTHON_EXE=python

"%PYTHON_EXE%" EDA/scripts/run_eda_stage4.py %DATASET_NAME%
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
