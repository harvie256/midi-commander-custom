# MIDI Commander Studio

MIDI Commander Studio is a cross-platform local browser application backed by Python. It is designed to minimize Terminal or Command Prompt use while preserving compatibility with the original firmware and CSV tooling.

## Support status

- **macOS:** tested end-to-end with a physical MIDI Commander, including DFU firmware installation, normal-mode MIDI detection, validation, and configuration upload.
- **Windows 10/11 (64-bit):** launcher and implementation are included and exercised by automated checks, but physical DFU and MIDI upload testing is pending. Treat Windows support as beta.

## Normal use on macOS

Double-click `Launch MIDI Commander Studio.command` in the repository root. The launcher creates `.studio-venv` on first use, installs the Python dependencies privately, starts the local service, and opens the browser.

The application has three workspaces:

- **Editor** — edit eight banks, eight buttons per bank, and up to ten commands per button. Projects autosave locally in the browser. Save a `.mcs.json` project to keep friendly button labels; export CSV for compatibility with the original uploader.
- **Device** — select CoreMIDI input/output endpoints, test commands, validate the packed 2,688-byte configuration, and upload it over SysEx. The pedal must be running the custom firmware in normal mode.
- **Firmware** — check for `dfu-util`, verify `0483:df11 / alt 0 / Internal Flash`, and install only the bundled custom DFU. This workflow requires explicit recovery confirmation.

Use the power button in the top-right corner to stop the local service. If needed, double-click `Stop MIDI Commander Studio.command`.

## Normal use on Windows

Install Python 3 with **Add Python to PATH** enabled, extract the repository, and double-click `Launch MIDI Commander Studio.cmd`. The launcher creates `.studio-venv-windows`, installs dependencies privately, hides the local backend window, and opens the Studio in the default browser.

Windows hardware testing is still pending. Keep a stock recovery file and review the Windows guide before attempting the first firmware installation.

Use the power button in the top-right corner to stop the local service. If needed, double-click `Stop MIDI Commander Studio.cmd`. The PowerShell files contain the implementation; the `.cmd` wrappers let users launch them without changing their PowerShell execution policy.

The Firmware page downloads a pinned official 64-bit `dfu-util` build from SourceForge into the ignored `.studio-tools` directory and verifies its SHA-256 checksum before extraction. No third-party executable is committed to this repository. Windows must associate the pedal's DFU-mode `STM32 BOOTLOADER` interface (`0483:df11`) with WinUSB; follow [`docs/WINDOWS.md`](../docs/WINDOWS.md) if the target is not detected.

## Architecture

- `studio/frontend/src` — React + TypeScript user interface.
- `studio/frontend/dist` — production build served by Python; Node.js is not needed for normal use.
- `studio/backend` — FastAPI service, project/CSV conversion, validation, MIDI upload, and DFU orchestration.
- `studio/requirements.txt` — isolated runtime dependencies.
- `Launch MIDI Commander Studio.cmd` / `.ps1` — Windows setup and launcher.
- `Launch MIDI Commander Studio.command` — macOS setup and launcher.

The backend reuses `python/lib/settingsBinaryPacker.py` and `python/lib/cmdBinaryPacker.py`, so packed configurations match the existing firmware format.

## Development

Backend:

```bash
cd /path/to/midi-commander-custom
python3 -m venv .studio-venv
source .studio-venv/bin/activate
python -m pip install -r studio/requirements.txt
python -m studio.backend.app
```

Frontend development server:

```bash
cd studio/frontend
npm install
npm run dev
```

Production build:

```bash
cd studio/frontend
npm run build
```

The Vite development server proxies `/api` to `http://127.0.0.1:8765`.

## Cross-platform checks

The GitHub Actions workflow in `.github/workflows/studio.yml` runs backend tests and the frontend production build on Windows, macOS, and Linux. CI confirms software compatibility only; it cannot validate physical USB MIDI or DFU behavior. macOS hardware testing has passed, while Windows hardware testing remains pending.
