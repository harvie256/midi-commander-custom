@echo off

REM Find the last dfu file alphabetically in the DFU_OUT folder and upload that.
for /f "delims=" %%a in ('dir /b /a-d /on DFU_OUT\*.dfu') do set lastone=%%a

echo Attempting to upload %lastone%

MidiCommander_DFU_APP\DfuSeCommand.exe -c --al 0 -d --v --fn DFU_OUT\%lastone%
pause