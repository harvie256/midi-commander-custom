# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Replacement firmware for the MeloAudio MIDI Commander (a MIDI foot controller), plus the host-side tooling to configure it. Three pieces that must stay in sync:

1. **Firmware** — `MIDI_Commander_Custom/`, a CMake project for an STM32F103RET (256 KiB+ flash, 12 MHz crystal, SSD1306 OLED on I2C1 @0x3C, MIDI DIN out on USART2). Still carries a CubeMX `.ioc`.
2. **MIDI Commander Studio** — `studio/`, a local-only GUI (FastAPI backend + React frontend, opened in the browser) and the **only** supported way to configure the pedal. Launched by the `Launch MIDI Commander Studio.*` scripts at the repo root.
3. **DFU packaging** — `DFU/bin_to_dfu.py` wraps a build into a `.dfu`; `DFU/MidiCommander_DFU_APP/` holds the vendored ST Windows tools and drivers.

There used to be a fourth: a `python/CSV_to_Flash.py` CLI that packed a CSV spreadsheet, sharing its encoder with Studio. It was deleted along with all CSV import/export, because planned features change the configuration model in ways the CSV layout could not follow without becoming a compatibility burden. Consequences worth knowing:

- **Projects are `.mcs.json` only.** That is just a serialised `StudioProject`, saved and loaded entirely client-side. Anyone still holding a CSV needs a Studio build from before the removal to convert it.
- **There is no scripted/headless configuration path.** Everything goes through the GUI.
- The encoder is no longer shared with anything, so it takes the typed model directly and `pandas` is gone.

The firmware has no tests; verification is on hardware. Studio's backend has pytest coverage under `studio/backend/tests/`, and `.github/workflows/studio.yml` runs it plus a frontend type-check and build on all three OSes — but **only** on changes under `studio/` and the launcher scripts. Nothing in CI builds the firmware.

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

**Linux prerequisite for any Python work here:** `python-rtmidi` is compiled from source whenever no wheel matches your Python (there is none for 3.14, which is what Ubuntu 26.04 ships), so this bites on new distributions rather than being a one-off. It needs `libasound2-dev`; JACK is optional. **Install `libjack-jackd2-dev`, never `libjack-dev`** — the latter is JACK1, and apt satisfies it by removing the JACK2 runtime the rest of the desktop audio stack depends on.

```
sudo apt install -y libasound2-dev libjack-jackd2-dev
```

A venv is also not optional on current Debian/Ubuntu: the system interpreter is marked externally managed (PEP 668), so `pip install` into it is refused with or without `sudo`, and `--user` is refused too. The launchers already do this correctly.

Python is formatted with Black and type-checked with mypy in basic mode (`.vscode/`); mido's dynamic symbols require `# type: ignore` on its call sites.

**Studio:** the launcher scripts are the supported entry point — they create the venv, install `studio/requirements.txt`, start the backend detached, and open the browser at `http://127.0.0.1:8765`. Each OS gets its own venv directory (`.studio-venv` on macOS, `.studio-venv-linux`, `.studio-venv-windows`) because a venv is not portable across platforms; all three are gitignored, along with `.studio-runtime/` (logs and the server PID) and `.studio-tools/`.

To work on it directly:

```
python3 -m venv .studio-venv-linux
.studio-venv-linux/bin/python -m pip install -r studio/requirements.txt pytest
.studio-venv-linux/bin/python -m studio.backend.app     # run from the repo root; --host/--port to override
.studio-venv-linux/bin/python -m pytest -q studio/backend/tests
```

The backend must be started from the repo root — it is a package (`studio.backend.app`), and `device_service.py` resolves `REPO_ROOT` by walking up two parents to reach `DFU/` and the firmware build directory.

Frontend work needs Node:

```
cd studio/frontend && npm ci
npm run dev      # Vite on 127.0.0.1:5173, proxying /api to the backend on 8765
npm run lint     # tsc --noEmit over both tsconfigs; `build` runs the same check first
npm run build
```

**`studio/frontend/dist/` is committed on purpose.** `app.py` mounts it as static files and serves `index.html` as a catch-all, and no launcher runs `npm` — an end user gets the GUI with Python alone. So a frontend source change is not live until you rebuild *and commit the rebuilt `dist/`*. Two consequences: a source edit without a rebuild silently does nothing, and the bundle hashes in `dist/assets/` move whenever the output changes. The build *is* reproducible — rebuilding an unchanged tree on Node 22 reproduces `dist/` byte for byte — so unexpected churn there means a real difference (a dependency drift or a different Node major), not build noise. Only `index-*.js`/`index-*.css` should move for an app-code change; churn in the font assets means something else shifted.

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

`studio/backend/flash_packer.py` is the **only** host-side encoder. It takes a `StudioProject` straight from `models.py` and emits the flash image; `Core/Src/midi_cmds.c` decodes it. One encoder, one direction, no intermediate representation.

It used to be two pandas-coupled modules under `python/lib/`, shaped around CSV rows (`row.loc[row.index.str.startswith("A_")]`), with Studio converting its typed model *back* into CSV-shaped DataFrames purely to feed them. Deleting the CSV path removed that whole layer — along with `pandas`, and the "column names are a contract" hazard.

Constants are mirrored from the firmware by hand, and **the mirroring is enforced by tests** rather than convention. `test_flash_packer.py` greps the C directly:

- `test_command_nibbles_match_firmware_defines` — every `CMD_*_NIBBLE` and `GLOBAL_SETTINGS_*` against `midi_defines.h`
- `test_layout_matches_firmware_header` — `MIDI_ROM_CMD_SIZE` and `MIDI_NUM_COMMANDS_PER_SWITCH` against `flash_midi_settings.h`, the `+32+96` pointer offsets and `FLASH_SETTINGS_NO_PAGES` against `flash_midi_settings.c`, and that the image still fits the erased region

Change a `#define` in the firmware without updating the packer and CI fails. That is the only automated link between the C and Python halves of this repo, so keep those tests grepping real source rather than restating values.

`test_reference_configuration_packs_to_known_bytes` pins the output against a golden image in `tests/fixtures/rc600_reference.json`, captured from the pandas implementation before it was deleted. It is the regression guard for the rewrite and for any future change to the encoder.

Encoding conventions live as a docstring in `flash_packer.py`. The one worth repeating: the firmware's "no value" test is `> 0x7F`, not `== 0x80` — `midi_cmds.c` returns early when `pRom[3] > 0x7F` for a CC off-value, and treats bank-select bytes as present only when `< 0x80`. The old CSV path wrote `255` for a suppressed CC off-value; the packer now writes `0x80`. Both suppress identically.

Encoding conventions worth knowing: byte 0 is command nibble | channel; the toggle flag is the top bit of byte 1; the "no value" sentinel is `0x80` (used to suppress bank-select bytes in PC commands and the off-value in CC); note/PB duration is byte 3 in 10 ms units.

### Config transfer protocol (USB SysEx)

`USB_DEVICE/App/usbd_midi_if.c` implements the device side and `studio/backend/device_service.py` the host side — one each, since the CLI was removed. `device_service.py` re-declares the opcodes (`ERASE_FLASH = 52`, `WRITE_FLASH = 54`, `RESET = 60`, …) rather than deriving them from `midi_defines.h`, and unlike the packer constants nothing tests that mirroring.

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

[`PACKAGING-OPTIONS.md`](PACKAGING-OPTIONS.md) records two candidate directions for replacing the launcher-plus-browser delivery model (a Tauri desktop app, or a static web app using Web MIDI/WebUSB). Exploratory — nothing there is decided, but read it before proposing a third.

A localhost web app, not a desktop app: `studio/backend/app.py` is a FastAPI server bound to `127.0.0.1:8765` that serves both the JSON API and the prebuilt React bundle, and the launcher just opens a browser at it. There is no authentication and no CORS — binding to loopback *is* the security model, so don't add a `--host 0.0.0.0` default or widen it casually. `POST /api/shutdown` calls `os._exit(0)` behind a 0.4 s timer (so the HTTP response gets flushed first); that is what the `Stop MIDI Commander Studio.*` scripts and the UI's quit button hit.

Route order matters in `app.py`: the static-file mount and the `@app.get("/{full_path:path}")` catch-all that serves `index.html` are registered *after* every API route, at the bottom of the module. A new endpoint declared below them is shadowed by the catch-all and returns HTML.

**Three pages, three backends:**

- **Editor** (`config_service.py` + `flash_packer.py`) — pure data: validate, then pack. `validate_project()` returns a flat list of `{level, path, message}`; `error` blocks packing and upload, `warning` does not. It is the only place the firmware's field limits are enforced host-side (16-char config name, 4/8-char bank names, 8 banks × 8 buttons × ≤10 commands, channel 1–16, duration a multiple of 10 ms up to 1270). `config_service.pack_project()` validates and then delegates to `flash_packer.pack()`, which assumes a valid project — call the former unless you have already validated.
- **Device** (`device_service.py`) — MIDI. Scans ports via mido and calls anything with `STM` in the name compatible; uploads over the SysEx protocol above; `test_command()` sends a single command live for audition, expanding one stored command into the MIDI messages the firmware would emit.
- **Firmware** (`device_service.py`) — DFU. Checks for `dfu-util`, can fetch it on Windows (pinned SourceForge URL, SHA-256 verified before extraction) or `brew install` it on macOS, and shells out to install firmware. Linux is deliberately manual — install `dfu-util` from your distro.

**Which firmware gets installed:** `resolve_firmware()` prefers `MIDI_Commander_Custom/build/DFU Release/MIDI_Commander_Custom.dfu` when it exists and falls back to the committed `DFU/DFU_OUT/generated-20220424-163714.dfu`, so a firmware change reaches the pedal instead of being silently ignored. `POST /api/firmware/install` takes an optional `source` (`"built"` / `"bundled"`) to pin the choice; omitting it means auto. `firmware_status()` reports the resolution as `firmwareSource` and lists both candidates with their mtimes in `firmwareSources`. Consequence worth knowing: **a stale `build/` directory wins.** It is the same directory `cmake --build` writes, so `rm -rf "build/DFU Release"` is how you go back to the bundled file.

The Install step renders a radio picker over `firmwareSources`, filtered to the files that exist, and only shows it when there is more than one — so a user who has never built the firmware sees the same single-file panel as before. The frontend sends `source: null` until the user picks explicitly, which is what keeps auto-resolution and an explicit choice distinguishable on the wire.

The `--device` argument in `_firmware_install_command()` is derived per file, not hardcoded. dfu-util validates the file's own DfuSe suffix identity against the *runtime* half of `--device` and matches the live target against the *DFU-mode* half, and those differ between the two files — the bundled one records `0483:0000`, a freshly packed build records `0483:df11`. `_dfu_suffix_ids()` reads the runtime half out of the file's trailing 16-byte suffix so suffix validation stays on rather than being bypassed with a force flag; a file with no `UFD` signature is refused outright.

**Long operations are jobs.** Uploading, installing `dfu-util`, and installing firmware all return a `jobId` immediately and run on a daemon thread (`jobs.py`); the frontend's `useJob` hook polls `GET /api/jobs/{id}` every 500 ms until `completed`/`failed`. The store is a plain in-memory dict with no eviction — jobs die with the process, which is fine for a single-user local tool. Backend code inside a job reports by calling `job.log()`/setting `job.progress`; raising is how you fail it, and the exception message is what the user sees.

**Project state lives in the browser.** `useStudioProject` keeps the whole project in `localStorage` under `midi-commander-studio:project:v1`, debounced 250 ms, and revalidates against the server 180 ms after every edit. The server holds no project state at all — every endpoint takes the full `StudioProject` in the request body. Clearing site data loses unsaved work, and since the CSV removal the `.mcs.json` project file is the *only* way to get a configuration out of the browser — it is just the serialised `StudioProject`, saved and reloaded entirely client-side with no endpoint behind it. Open/Save project sit in the header for that reason.

`models.py` is the schema shared across all of it: pydantic models on the backend, hand-mirrored in `studio/frontend/src/types.ts`. They are not generated from each other, so a field added to one must be added to the other.

Note the model/wire unit split that survived the CSV removal: `durationMs` is milliseconds in the model but 10 ms units on the wire, and `suppressOff: true` becomes a byte above `0x7F`.

Sizes are derived, not restated. `flash_packer.FLASH_CONTENT_SIZE` computes the 2688-byte image from the layout constants, so `pack()` and `upload_configuration()` both check the same derivation rather than a literal.

## CubeMX-generated code

`MIDI_Commander_Custom.ioc` regenerates `main.c`, `stm32f1xx_it.c`, `stm32f1xx_hal_msp.c`, and the USB_DEVICE files. Regenerating overwrites everything outside `/* USER CODE BEGIN X */ ... /* USER CODE END X */` markers.

It still carries `ProjectManager.TargetToolchain=STM32CubeIDE`, so a regeneration would re-emit the `.cproject`/`.project` files that the CMake conversion removed. Switching it to CMake generation is a deliberate, untested change — CubeMX knows nothing about the vendored ssd1306 fork or the custom USB MIDI class, so its `CMakeLists.txt` would not be a drop-in replacement for the hand-written one.

Hand edits that live *outside* the USER CODE markers and would be lost to a regeneration:

- `VECT_TAB_OFFSET` in `system_stm32f1xx.c`
- The MIDI class (`Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/`) — CubeMX only knows about the AUDIO class this was derived from

Pin names (`SW_1_Pin`, `LED_A_GPIO_Port`, …) come from the `.ioc` and are the vocabulary `switch_router.c` is written in.

## The removed CSV path

Configuration was originally a CSV spreadsheet (a Google Sheet template) fed to `python/CSV_to_Flash.py`. That tool, the `python/` directory, and Studio's CSV import/export are all gone; `git log -- python/` has the history if you need the old format.

Don't reintroduce it. It is not a small feature: it was two divergent parsers, a `pandas` dependency, a column-name contract between the CSV headers and the encoder, and a set of representational quirks (a suppressed CC off-value spelled `255`, durations in 10 ms units) that existed only because the wire format had to survive a round-trip through spreadsheet columns. The planned configuration-model changes are what made that cost unpayable.

The RC-600 configuration that used to live at `python/MeloConfig_10_Cmds - RC-600.csv` survives as a `StudioProject` in `studio/backend/tests/fixtures/rc600_reference.json`, where it now serves as the encoder's golden-image fixture.
