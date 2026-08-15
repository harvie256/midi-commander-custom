# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Replacement firmware for the MeloAudio MIDI Commander (a MIDI foot controller), plus the host-side tooling to configure it. Three pieces that must stay in sync:

1. **Firmware** — `MIDI_Commander_Custom/`, an STM32CubeIDE project for an STM32F103RET (256 KiB+ flash, 12 MHz crystal, SSD1306 OLED on I2C1 @0x3C, MIDI DIN out on USART2).
2. **Config tool** — `python/CSV_to_Flash.py`, packs a CSV config into the firmware's binary layout and pushes it over USB MIDI SysEx.
3. **DFU packaging** — `DFU/`, Windows ST DfuSe tools plus `BuildDFUAutomation.py` to wrap a build into a `.dfu`.

There is no test suite anywhere in the repo. Verification is done on hardware.

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

Output lands in `build/<preset>/` as `.elf`, `.hex` (consumed by `DFU/BuildDFUAutomation.py`), and `.bin` (consumed by `dfu-util`). `-DTOOLCHAIN_PREFIX=/path/to/bin/` selects a compiler that isn't on `PATH`.

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

**Flashing a build:**
- Windows: `python DFU/BuildDFUAutomation.py` (needs `pywinauto`; drives `DfuFileMgr.exe` through its GUI, consumes the `.hex`), then `DFU/DownloadToMidiCommandByDFU.bat`.
- macOS/Linux: `dfu-util --alt 0 -s 0x8003000 --download "MIDI_Commander_Custom/build/DFU Release/MIDI_Commander_Custom.bin"` — pass the load address explicitly since `dfu-util` can't build a `.dfu`.
- Device enters DFU mode by holding `bank down` + `D` while pressing power.

**Python tooling:**

```
python3 -m pip install -r python/requirements.txt
python3 python/CSV_to_Flash.py <config.csv>
```

On Linux, `python-rtmidi` needs `libjack-dev` and `libasound2-dev` first — see `python/linux-prerequisites.sh`. Python is formatted with Black and type-checked with mypy in basic mode (`.vscode/`); mido's dynamic symbols require `# type: ignore` on its call sites.

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

Encoding conventions worth knowing: byte 0 is command nibble | channel; the toggle flag is the top bit of byte 1; the "no value" sentinel is `0x80` (used to suppress bank-select bytes in PC commands and the off-value in CC); note/PB duration is byte 3 in 10 ms units.

### Config transfer protocol (USB SysEx)

`USB_DEVICE/App/usbd_midi_if.c` implements the device side; `CSV_to_Flash.py` the host side. Private-use manufacturer ID `0x7D`. Erase (52) requires the check words `0x42 0x24` and replies 53; write (54) carries a 16-byte-page address as two 7-bit bytes followed by 16 bytes split into 32 nibbles, and replies 55; reset (60) calls `NVIC_SystemReset()`. The host waits for each reply before sending the next chunk. Nibble-splitting exists because SysEx data bytes must stay under 0x80.

The same file also handles realtime passthrough: USB clock/start/stop bytes are forwarded to the serial port when `GLOBAL_SETTINGS_REALTIME_PASS` is set.

### MIDI output paths

Every send in `midi_cmds.c` fans out to both transports, which have different buffering needs:

- **USB** — assembled into the single `midi_usb_assembly_buffer` and handed to the stack, which copies it into the endpoint buffer immediately.
- **Serial (USART2 + DMA)** — far slower, so there is a pool of `2 * MIDI_NUM_COMMANDS_PER_SWITCH` mailbox buffers. Slot claiming runs inside `__disable_irq()`/`__enable_irq()`; `HAL_UART_TxCpltCallback` frees the finished slot and kicks off the next. Exhaustion returns `ERROR_BUFFERS_FULL`, which `switch_router.c` turns into `Error("Buffers full")`.

`Error(msg)` (in `main.c`) prints to the OLED and then spins forever with interrupts off — it is a terminal halt, not a warning.

### Display

`Middlewares/stm32-ssd1306-master/` is a **vendored and modified** fork of afiskon/stm32-ssd1306. The modification is the point: screen updates are pushed one page at a time by `ssd1306_tick()` from SysTick, each page a single `HAL_I2C_Mem_Write_DMA` that carries the page/column commands and the pixel data together. Do not replace it with upstream — the DMA/tick machinery would be lost.

## CubeMX-generated code

`MIDI_Commander_Custom.ioc` regenerates `main.c`, `stm32f1xx_it.c`, `stm32f1xx_hal_msp.c`, and the USB_DEVICE files. Regenerating overwrites everything outside `/* USER CODE BEGIN X */ ... /* USER CODE END X */` markers.

It still carries `ProjectManager.TargetToolchain=STM32CubeIDE`, so a regeneration would re-emit the `.cproject`/`.project` files that the CMake conversion removed. Switching it to CMake generation is a deliberate, untested change — CubeMX knows nothing about the vendored ssd1306 fork or the custom USB MIDI class, so its `CMakeLists.txt` would not be a drop-in replacement for the hand-written one.

Hand edits that live *outside* the USER CODE markers and would be lost to a regeneration:

- `VECT_TAB_OFFSET` in `system_stm32f1xx.c`
- The MIDI class (`Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/`) — CubeMX only knows about the AUDIO class this was derived from

Pin names (`SW_1_Pin`, `LED_A_GPIO_Port`, …) come from the `.ioc` and are the vocabulary `switch_router.c` is written in.

## Configuration CSV format

The template is a Google Sheet (linked in `README.md`); `python/MeloConfig_10_Cmds - RC-600.csv` is a checked-in copy. The parser splits the file into sections on lines containing `*` — `Global_Settings`, `Bank_Naming`, `Button_Settings` — and each becomes a pandas DataFrame. Per-command columns are prefixed `A_` through `J_` for the 10 commands. Note that comment stripping drops any line *containing* `#`, not just lines starting with it.
