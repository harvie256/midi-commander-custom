# MIDI Commander Studio on Windows

This guide covers Windows 10 and Windows 11 on a 64-bit PC. MIDI Commander Studio runs locally and does not send project data to a remote service.

> **Beta status:** The Windows launcher, dependency setup, UI, backend tests, and CI are implemented, but firmware installation and configuration upload have not yet been tested with a physical MIDI Commander on Windows. Keep a stock firmware recovery file and report Windows results or issues to the project before treating this workflow as production-tested.

## What you need

- Python 3 from [python.org](https://www.python.org/downloads/windows/), installed with **Add Python to PATH** enabled.
- A USB data cable, not a charging-only cable.
- Internet access for the first Studio launch and the first `dfu-util` download.
- A stock `.dfu` recovery file before replacing the pedal firmware.

## Start Studio

1. Download the repository ZIP from GitHub and extract it to a writable folder such as `Documents\midi-commander-custom`.
2. Double-click `Launch MIDI Commander Studio.cmd`.
3. If SmartScreen appears, confirm the repository source, choose **More info**, and then **Run anyway**.
4. Wait while the launcher creates `.studio-venv-windows` and installs the Python components on first use.
5. Studio opens at `http://127.0.0.1:8765` in the default browser.

The launcher window closes once Studio is ready. To stop the local service, use the power button in Studio or double-click `Stop MIDI Commander Studio.cmd`.

## Install the custom firmware

Configuration upload works only after the custom firmware is installed.

1. Open Studio's **Firmware** page.
2. Click **Download dfu-util**. Studio downloads the pinned official build from the [dfu-util project](https://dfu-util.sourceforge.net/), verifies its SHA-256 checksum, and stores it under `.studio-tools\dfu-util`.
3. Turn the MIDI Commander off.
4. Hold **D + Bank Down** while turning it on. The display should remain blank and LED 3 should illuminate.
5. Click **Check again**.

### If Windows does not detect the DFU target

`dfu-util` requires a libusb-compatible Windows driver. Install WinUSB only for the pedal's DFU-mode interface:

1. Download [Zadig from its official site](https://zadig.akeo.ie/).
2. Keep the pedal connected in DFU mode.
3. In Zadig, choose **Options → List All Devices**.
4. Select **STM32 BOOTLOADER** and verify its USB ID is `0483:df11`.
5. Select **WinUSB** as the target driver and choose **Install Driver** or **Replace Driver**.
6. Close Zadig and click **Check again** in Studio.

Selecting the wrong USB device in Zadig can disrupt another device, so verify both the name and USB ID before changing the driver.

When Studio reports `0483:df11 · alt 0 · Internal Flash`, confirm that you have a recovery file and choose **Install firmware**. Do not disconnect or power off the pedal while the firmware job is running. When it completes, power-cycle the pedal normally.

## Upload a configuration

1. Start the pedal normally and connect it by USB.
2. Open Studio's **Device** page and click **Check again**.
3. Select the pedal's MIDI input and output ports.
4. Return to **Editor** and optionally send a test command.
5. Open **Device**, confirm validation passes, and choose **Upload configuration**.
6. Leave the pedal connected until Studio reports completion and the pedal restarts.

## Troubleshooting

### Python was not found

Re-run the Python installer, enable **Add Python to PATH**, and then start Studio again. The launcher prefers the standard Windows `py.exe` launcher when available.

### The browser did not open

Visit `http://127.0.0.1:8765` manually. Logs are stored in `.studio-runtime\server-windows.log` and `.studio-runtime\server-windows-error.log`.

### No MIDI ports are listed

Make sure the pedal is running normally, not in DFU mode. Reconnect the USB cable, try another data cable or port, and click **Check again**.

### Reset the local Studio installation

Stop Studio and delete `.studio-venv-windows`. The launcher recreates it on the next start. Deleting `.studio-tools` also removes the locally downloaded `dfu-util`; Studio will offer to download it again.
