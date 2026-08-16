# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Replacement firmware for the MeloAudio MIDI Commander (a MIDI foot controller), plus the host-side tooling to configure it. Four pieces that must stay in sync:

1. **Firmware** — `MIDI_Commander_Custom/`, a CMake project for an STM32F103RET (256 KiB+ flash, 12 MHz crystal, SSD1306 OLED on I2C1 @0x3C, MIDI DIN out on USART2). Still carries a CubeMX `.ioc`.
2. **Config tool** — `python/CSV_to_Flash.py`, packs a CSV config into the firmware's binary layout and pushes it over USB MIDI SysEx.
3. **DFU packaging** — `DFU/bin_to_dfu.py` wraps a build into a `.dfu`; `DFU/MidiCommander_DFU_APP/` holds the vendored ST Windows tools and drivers.
4. **MIDI Commander Studio** — `studio/`, a local-only GUI (FastAPI backend + React frontend, opened in the browser) that wraps 2 and 3 for people who don't want a CSV and a terminal. Launched by the `Launch MIDI Commander Studio.*` scripts at the repo root.

The firmware and the CLI tooling have no tests; verification is on hardware. Studio's backend has pytest coverage under `studio/backend/tests/`, and `.github/workflows/studio.yml` runs it plus a frontend type-check and build on all three OSes — but **only** on changes under `studio/`, `python/`, and the launcher scripts. Nothing in CI builds the firmware.

## Building

**Firmware:** CMake + `arm-none-eabi-gcc`, driven by `MIDI_Commander_Custom/CMakePresets.json`. Two presets, matching the STM32CubeIDE configurations this replaced:

| Preset | `CMAKE_BUILD_TYPE` | Linker script | Flash origin | Use |
|---|---|---|---|---|
| `Debug` | Debug (`-O0`) | `STM32F103RETX_FLASH.ld` | `0x8000000` | ST-Link debugging via SWD (see `HardwareNotes.txt` for the P3 pinout) |
| `DFU Release` | Release (`-O2`) | `STM32F103RETX_FLASH_DFU.ld` | `0x8003000` | Loading over the stock ST DFU bootloader |

```
cd MIDI_Commander_Custom
cmake --preset "DFU Release" && cmake --build --preset "DFU Release"
```

Output lands in `build/<preset>/` as `.elf`, `.hex`, `.bin` (what `dfu-util` loads), and — for `DFU Release` only — a packed `.dfu`. `-DTOOLCHAIN_PREFIX=/path/to/bin/` selects a compiler that isn't on `PATH`.

The DFU offset lives in **three** places that must move together, and the third is easy to miss:

1. `ORIGIN` in `STM32F103RETX_FLASH_DFU.ld`
2. `VECT_TAB_OFFSET` (`0x3000`) in `Core/Src/system_stm32f1xx.c`
3. **`-DUSER_VECT_TAB_ADDRESS`** — the `#if` guard around (2). It is never defined in source; it comes from the build config, so `SystemInit()` only writes `SCB->VTOR` when it is set

`CMakeLists.txt` therefore sets the linker script and that define together under a single `DFU_BOOTLOADER_OFFSET` option — keep it that way. Setting one without the other yields firmware that flashes and boots but faults on the first interrupt. To verify a DFU build is correct without hardware:

```
arm-none-eabi-readelf -S "build/DFU Release/MIDI_Commander_Custom.elf" | grep isr_vector   # 08003000
arm-none-eabi-objdump -d "build/DFU Release/MIDI_Commander_Custom.elf" --disassemble=SystemInit
```

The disassembly must store `0x08003000` to `0xE000ED08`; in a `Debug` build `SystemInit` is a no-op.

**Packing a `.dfu`:** `DFU/bin_to_dfu.py` — pure Python, no ST tools. The `DFU Release` build runs it automatically as a post-build step (guarded by `find_package(Python3)`, warning rather than failing if absent); run it by hand as `python3 DFU/bin_to_dfu.py <build.hex> -o out.dfu` to repack without rebuilding. A `.hex` carries its own load address; a `.bin` needs `-a 0x8003000`. Output is byte-identical to `DfuFileMgr.exe` apart from the 255-byte target-name field, where ST's tool emits uninitialised heap past `"ST..."` and this writes zero padding.

Only the DFU variant gets packed, deliberately — a `Debug` build is linked at `0x8000000`, so a `.dfu` of it would overwrite the bootloader if uploaded.

**Flashing a build:** `dfu-util` is the single supported path on all three operating systems.

- `dfu-util --alt 0 -s 0x8003000 --download "MIDI_Commander_Custom/build/DFU Release/MIDI_Commander_Custom.bin"` — the `.bin` needs the address named explicitly; the `.dfu` carries it, so `dfu-util --alt 0 --download <file.dfu>` also works.
- Device enters DFU mode by holding `bank down` + `D` while pressing power.
- `DFU/MidiCommander_DFU_APP/` holds ST's DfuSe tools and Windows drivers. Nothing in the repo drives them; they are retained only because returning to stock MeloAudio firmware needs a DfuSe-based updater, and on Windows that means switching the USB driver back from the WinUSB one that dfu-util requires. Don't reintroduce them into any build or flash workflow.

**Python tooling:**

```
python3 -m pip install -r python/requirements.txt
python3 python/CSV_to_Flash.py <config.csv>
```

On Linux, `python-rtmidi` needs `libjack-dev` and `libasound2-dev` first — see `python/linux-prerequisites.sh`. Python is formatted with Black and type-checked with mypy in basic mode (`.vscode/`); mido's dynamic symbols require `# type: ignore` on its call sites.

**Studio:** the launcher scripts are the supported entry point — they create the venv, install `studio/requirements.txt`, start the backend detached, and open the browser at `http://127.0.0.1:8765`. Each OS gets its own venv directory (`.studio-venv` on macOS, `.studio-venv-linux`, `.studio-venv-windows`) because a venv is not portable across platforms; all three are gitignored, along with `.studio-runtime/` (logs and the server PID) and `.studio-tools/`.

To work on it directly:

```
python3 -m venv .studio-venv-linux
.studio-venv-linux/bin/python -m pip install -r studio/requirements.txt pytest
.studio-venv-linux/bin/python -m studio.backend.app     # run from the repo root; --host/--port to override
.studio-venv-linux/bin/python -m pytest -q studio/backend/tests
```

The backend must be started from the repo root — it is a package (`studio.backend.app`), and `config_service.py`/`device_service.py` resolve `REPO_ROOT` by walking up two parents to reach `python/lib/` and `DFU/`.

Frontend work needs Node:

```
cd studio/frontend && npm ci
npm run dev      # Vite on 127.0.0.1:5173, proxying /api to the backend on 8765
npm run lint     # tsc --noEmit over both tsconfigs; `build` runs the same check first
npm run build
```

**`studio/frontend/dist/` is committed on purpose.** `app.py` mounts it as static files and serves `index.html` as a catch-all, and no launcher runs `npm` — an end user gets the GUI with Python alone. So a frontend source change is not live until you rebuild *and commit the rebuilt `dist/`*. Two consequences: the bundle hashes in `dist/assets/` churn on every build, and a source edit without a rebuild silently does nothing.

## Architecture

### Firmware control flow

Bare-metal super-loop, no RTOS. `main()` initialises peripherals and then does nothing but call `handle_switches()` forever. The real work is split between SysTick and that loop:

- **SysTick (1 kHz), in `stm32f1xx_it.c`** calls two hand-added hooks: `sw_scan()` and `ssd1306_tick()`. Switch pins are spread across GPIOA/B/C and not all are interrupt-capable, so switches are *polled* — each tick XORs the port against the previous state, ORs changes into `port_X_switches_changed`, and sets a 10 ms `debounce_counter`. The `f_sys_config_complete` flag gates scanning until init finishes.
- **Main loop** consumes those change flags in `switch_router.c` and dispatches MIDI.

Anything that blocks in the main loop delays switch handling and MIDI timing — this is why display updates are DMA-driven and why `midi_cmds.c` warns against drawing to the screen from the send path.

### Configuration storage and layout

Settings live in the MCU's **internal flash** (not the external EEPROM the stock firmware uses, so both firmwares coexist). `Core/Src/flash_midi_settings.c` fixes the region at `FLASH_BASE + 128 KiB`, spanning `FLASH_SETTINGS_NO_PAGES` (3) × 1 KiB pages, exposed as three pointers:

```
pGlobalSettings  +0     32 bytes   16 setting bytes + 16 ASCII config name
pBankStrings     +32    96 bytes   8 banks × (4-char large name + 8-char small name)
pSwitchCmds      +128   rest       8 pages × 8 switches × 10 commands × 4 bytes
```

Command lookup is pure pointer arithmetic — `get_rom_pointer(page, sw, cmd)` in `switch_router.c` and the equivalent inline expressions in `handle_switches()`. `MIDI_ROM_CMD_SIZE`, `MIDI_NUM_COMMANDS_PER_SWITCH`, and `MIDI_ROM_KEY_STRIDE` in `flash_midi_settings.h` define the stride.

### The C/Python wire contract

The 4-byte per-command encoding is **written** by `python/lib/cmdBinaryPacker.py` and **decoded** by `Core/Src/midi_cmds.c`. Nothing enforces agreement, so a change on one side needs a matching change on the other. Duplicated constants to keep aligned:

- Command-type nibbles (`CMD_PC_NIBBLE` etc.) — `Core/Inc/midi_defines.h` ↔ `cmdBinaryPacker.py`
- `MIDI_NUM_COMMANDS_PER_SWITCH` (10) — `flash_midi_settings.h` ↔ `cmdBinaryPacker.py`
- `GLOBAL_SETTINGS_*` indices — `midi_defines.h` ↔ `settingsBinaryPacker.py`
- `FLASH_SETTINGS_NO_PAGES` ↔ `ALLOWED_NUM_FLASH_PAGES` in `CSV_to_Flash.py` (the tool only warns on overflow)

Studio does **not** add a fourth encoder — `studio/backend/config_service.py` imports the same two packers (via a `sys.path` insert of `python/`) and feeds them pandas DataFrames shaped exactly like the ones `CSV_to_Flash.py` builds from a CSV. So the packers stay the single source of truth, but their *input column names* are now a contract too: `COMMAND_FIELDS` in `config_service.py` must match the `A_`…`J_` column suffixes `cmdBinaryPacker.pack_row()` reads.

Encoding conventions worth knowing: byte 0 is command nibble | channel; the toggle flag is the top bit of byte 1; the "no value" sentinel is `0x80` (used to suppress bank-select bytes in PC commands and the off-value in CC); note/PB duration is byte 3 in 10 ms units.

### Config transfer protocol (USB SysEx)

`USB_DEVICE/App/usbd_midi_if.c` implements the device side. There are **two** host-side implementations: `CSV_to_Flash.py` and `studio/backend/device_service.py`, which re-declares the same opcodes (`ERASE_FLASH = 52`, `WRITE_FLASH = 54`, `RESET = 60`, …) rather than importing them. A protocol change needs editing all three.

Private-use manufacturer ID `0x7D`. Erase (52) requires the check words `0x42 0x24` and replies 53; write (54) carries a 16-byte-page address as two 7-bit bytes followed by 16 bytes split into 32 nibbles, and replies 55; reset (60) calls `NVIC_SystemReset()`. The host waits for each reply before sending the next chunk. Nibble-splitting exists because SysEx data bytes must stay under 0x80.

The same file also handles realtime passthrough: USB clock/start/stop bytes are forwarded to the serial port when `GLOBAL_SETTINGS_REALTIME_PASS` is set.

### MIDI output paths

Every send in `midi_cmds.c` fans out to both transports, which have different buffering needs:

- **USB** — assembled into the single `midi_usb_assembly_buffer` and handed to the stack, which copies it into the endpoint buffer immediately.
- **Serial (USART2 + DMA)** — far slower, so there is a pool of `2 * MIDI_NUM_COMMANDS_PER_SWITCH` mailbox buffers. Slot claiming runs inside `__disable_irq()`/`__enable_irq()`; `HAL_UART_TxCpltCallback` frees the finished slot and kicks off the next. Exhaustion returns `ERROR_BUFFERS_FULL`, which `switch_router.c` turns into `Error("Buffers full")`.

`Error(msg)` (in `main.c`) prints to the OLED and then spins forever with interrupts off — it is a terminal halt, not a warning.

### Display

`Middlewares/stm32-ssd1306-master/` is a **vendored and modified** fork of afiskon/stm32-ssd1306. The modification is the point: screen updates are pushed one page at a time by `ssd1306_tick()` from SysTick, each page a single `HAL_I2C_Mem_Write_DMA` that carries the page/column commands and the pixel data together. Do not replace it with upstream — the DMA/tick machinery would be lost.

### MIDI Commander Studio

A localhost web app, not a desktop app: `studio/backend/app.py` is a FastAPI server bound to `127.0.0.1:8765` that serves both the JSON API and the prebuilt React bundle, and the launcher just opens a browser at it. There is no authentication and no CORS — binding to loopback *is* the security model, so don't add a `--host 0.0.0.0` default or widen it casually. `POST /api/shutdown` calls `os._exit(0)` behind a 0.4 s timer (so the HTTP response gets flushed first); that is what the `Stop MIDI Commander Studio.*` scripts and the UI's quit button hit.

Route order matters in `app.py`: the static-file mount and the `@app.get("/{full_path:path}")` catch-all that serves `index.html` are registered *after* every API route, at the bottom of the module. A new endpoint declared below them is shadowed by the catch-all and returns HTML.

**Three pages, three backends:**

- **Editor** (`config_service.py`) — pure data. Import/export the CSV format, validate, and pack. `validate_project()` returns a flat list of `{level, path, message}`; `error` blocks packing and upload, `warning` does not. It is the only place the firmware's field limits are enforced host-side (16-char config name, 4/8-char bank names, 8 banks × 8 buttons × ≤10 commands, channel 1–16, duration a multiple of 10 ms up to 1270).
- **Device** (`device_service.py`) — MIDI. Scans ports via mido and calls anything with `STM` in the name compatible; uploads over the SysEx protocol above; `test_command()` sends a single command live for audition, expanding one stored command into the MIDI messages the firmware would emit.
- **Firmware** (`device_service.py`) — DFU. Checks for `dfu-util`, can fetch it on Windows (pinned SourceForge URL, SHA-256 verified before extraction) or `brew install` it on macOS, and shells out to install firmware. Linux is deliberately manual — install `dfu-util` from your distro.

**Which firmware gets installed:** `resolve_firmware()` prefers `MIDI_Commander_Custom/build/DFU Release/MIDI_Commander_Custom.dfu` when it exists and falls back to the committed `DFU/DFU_OUT/generated-20220424-163714.dfu`, so a firmware change reaches the pedal instead of being silently ignored. `POST /api/firmware/install` takes an optional `source` (`"built"` / `"bundled"`) to pin the choice; omitting it means auto. `firmware_status()` reports the resolution as `firmwareSource` and lists both candidates with their mtimes in `firmwareSources`. Consequence worth knowing: **a stale `build/` directory wins.** It is the same directory `cmake --build` writes, so `rm -rf "build/DFU Release"` is how you go back to the bundled file.

The Install step's static label still reads "Bundled file", so `firmwareFile` carries the qualifier `"MIDI_Commander_Custom.dfu (local DFU Release build)"` rather than a bare filename — that keeps the panel truthful without a frontend rebuild. When the Install step grows a real source picker off `firmwareSources`, drop the qualifier and make `firmwareSource`/`firmwareSources` required in `types.ts` (they are optional today for the same reason).

The `--device` argument in `_firmware_install_command()` is derived per file, not hardcoded. dfu-util validates the file's own DfuSe suffix identity against the *runtime* half of `--device` and matches the live target against the *DFU-mode* half, and those differ between the two files — the bundled one records `0483:0000`, a freshly packed build records `0483:df11`. `_dfu_suffix_ids()` reads the runtime half out of the file's trailing 16-byte suffix so suffix validation stays on rather than being bypassed with a force flag; a file with no `UFD` signature is refused outright.

**Long operations are jobs.** Uploading, installing `dfu-util`, and installing firmware all return a `jobId` immediately and run on a daemon thread (`jobs.py`); the frontend's `useJob` hook polls `GET /api/jobs/{id}` every 500 ms until `completed`/`failed`. The store is a plain in-memory dict with no eviction — jobs die with the process, which is fine for a single-user local tool. Backend code inside a job reports by calling `job.log()`/setting `job.progress`; raising is how you fail it, and the exception message is what the user sees.

**Project state lives in the browser.** `useStudioProject` keeps the whole project in `localStorage` under `midi-commander-studio:project:v1`, debounced 250 ms, and revalidates against the server 180 ms after every edit. The server holds no project state at all — every endpoint takes the full `StudioProject` in the request body. Clearing site data loses unsaved work; that's why the UI offers CSV export and a `.mcs.json` project file (the latter is just the serialised `StudioProject`, saved and reloaded entirely client-side — there is no endpoint for it).

`models.py` is the schema shared across all of it: pydantic models on the backend, hand-mirrored in `studio/frontend/src/types.ts`. They are not generated from each other, so a field added to one must be added to the other.

Two encoding quirks that must round-trip through the CSV: a suppressed CC off-value is written as `255` in the CSV but is `suppressOff: true` in the model (`0x80` on the wire), and `durationMs` is milliseconds in the model but 10 ms units in the CSV column. Sizes are derived, not restated. `config_service.FLASH_CONTENT_SIZE` computes the 2688-byte image from the layout constants — and takes the command count from `cmdBinaryPacker.MIDI_NUM_COMMANDS_PER_SWITCH` rather than repeating it — so `pack_project()` and `upload_configuration()` both check against the same derivation. `test_flash_layout_matches_firmware_header` greps `flash_midi_settings.h`/`.c` for `MIDI_ROM_CMD_SIZE`, `MIDI_NUM_COMMANDS_PER_SWITCH`, the `+32+96` pointer offsets, and `FLASH_SETTINGS_NO_PAGES`, and fails if the Python side has drifted from the C. That is the one piece of the C/Python contract with actual CI enforcement; everything else in the section above is still convention only.

## CubeMX-generated code

`MIDI_Commander_Custom.ioc` regenerates `main.c`, `stm32f1xx_it.c`, `stm32f1xx_hal_msp.c`, and the USB_DEVICE files. Regenerating overwrites everything outside `/* USER CODE BEGIN X */ ... /* USER CODE END X */` markers.

It still carries `ProjectManager.TargetToolchain=STM32CubeIDE`, so a regeneration would re-emit the `.cproject`/`.project` files that the CMake conversion removed. Switching it to CMake generation is a deliberate, untested change — CubeMX knows nothing about the vendored ssd1306 fork or the custom USB MIDI class, so its `CMakeLists.txt` would not be a drop-in replacement for the hand-written one.

Hand edits that live *outside* the USER CODE markers and would be lost to a regeneration:

- `VECT_TAB_OFFSET` in `system_stm32f1xx.c`
- The MIDI class (`Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/`) — CubeMX only knows about the AUDIO class this was derived from

Pin names (`SW_1_Pin`, `LED_A_GPIO_Port`, …) come from the `.ioc` and are the vocabulary `switch_router.c` is written in.

## Configuration CSV format

The template is a Google Sheet (linked in `README.md`); `python/MeloConfig_10_Cmds - RC-600.csv` is a checked-in copy. The parser splits the file into sections on lines containing `*` — `Global_Settings`, `Bank_Naming`, `Button_Settings` — and each becomes a pandas DataFrame. Per-command columns are prefixed `A_` through `J_` for the 10 commands. Note that comment stripping drops any line *containing* `#`, not just lines starting with it.

There are two parsers for this format and they are not identical. `CSV_to_Flash.py` uses pandas and the `#`-anywhere rule above; Studio's `_read_sections()` in `config_service.py` uses the `csv` module and only skips rows whose *first cell* starts with `#`. Studio is also lenient where the CLI is not — it ignores unknown command types, rows with an out-of-range bank number, and missing columns, filling defaults instead of failing. A CSV that imports cleanly into Studio is therefore not proof that `CSV_to_Flash.py` will accept it, and vice versa. Studio's exporter writes the same section layout with a `# Generated by MIDI Commander Studio` header line.
