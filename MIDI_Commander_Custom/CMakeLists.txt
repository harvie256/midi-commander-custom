cmake_minimum_required(VERSION 3.22)

project(MIDI_Commander_Custom C ASM)

#
# Build variants
#
# The two variants match the build configurations of the STM32CubeIDE project
# this replaced:
#
#   DFU_BOOTLOADER_OFFSET=OFF -> "Debug",       linked at 0x8000000, for SWD
#   DFU_BOOTLOADER_OFFSET=ON  -> "DFU Release", linked at 0x8003000, for DFU
#
# The offset variant needs *two* things that must always move together: the
# offset linker script, and USER_VECT_TAB_ADDRESS, which is what makes
# SystemInit() relocate SCB->VTOR to match (see VECT_TAB_OFFSET in
# Core/Src/system_stm32f1xx.c). Setting the script without the define produces
# firmware that flashes and boots but faults on the first interrupt, so they are
# deliberately set in a single place below.
#
option(DFU_BOOTLOADER_OFFSET "Link for the DFU bootloader at 0x8003000" OFF)

if(DFU_BOOTLOADER_OFFSET)
    set(LINKER_SCRIPT ${CMAKE_SOURCE_DIR}/STM32F103RETX_FLASH_DFU.ld)
    set(VARIANT_DEFINES USER_VECT_TAB_ADDRESS)
else()
    set(LINKER_SCRIPT ${CMAKE_SOURCE_DIR}/STM32F103RETX_FLASH.ld)
    set(VARIANT_DEFINES)
endif()

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_EXTENSIONS ON)          # gnu11, as the CubeIDE project used
set(CMAKE_C_STANDARD_REQUIRED ON)

set(CMAKE_C_FLAGS_DEBUG   "-O0 -g3")
set(CMAKE_C_FLAGS_RELEASE "-O2 -g3")

add_executable(${PROJECT_NAME}
    Core/Startup/startup_stm32f103retx.s

    Core/Src/display.c
    Core/Src/flash_midi_settings.c
    Core/Src/main.c
    Core/Src/midi_cmds.c
    Core/Src/stm32f1xx_hal_msp.c
    Core/Src/stm32f1xx_it.c
    Core/Src/switch_router.c
    Core/Src/syscalls.c
    Core/Src/sysmem.c
    Core/Src/system_stm32f1xx.c

    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_cortex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_dma.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_exti.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_flash.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_flash_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_i2c.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_pcd.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_pcd_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_pwr.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_uart.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_ll_usb.c

    Middlewares/ST/STM32_USB_Device_Library/Core/Src/usbd_core.c
    Middlewares/ST/STM32_USB_Device_Library/Core/Src/usbd_ctlreq.c
    Middlewares/ST/STM32_USB_Device_Library/Core/Src/usbd_ioreq.c
    Middlewares/ST/STM32_USB_Device_Library/Class/AUDIO/Src/usbd_audio.c
    Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Src/usbd_midi.c

    Middlewares/stm32-ssd1306-master/ssd1306/ssd1306.c
    Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_fonts.c
    Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_tests.c

    USB_DEVICE/App/usb_device.c
    USB_DEVICE/App/usbd_audio_if.c
    USB_DEVICE/App/usbd_desc.c
    USB_DEVICE/App/usbd_midi_if.c
    USB_DEVICE/Target/usbd_conf.c
)

target_include_directories(${PROJECT_NAME} PRIVATE
    Core/Inc
    Drivers/STM32F1xx_HAL_Driver/Inc
    Drivers/STM32F1xx_HAL_Driver/Inc/Legacy
    Drivers/CMSIS/Device/ST/STM32F1xx/Include
    Drivers/CMSIS/Include
    Middlewares/ST/STM32_USB_Device_Library/Core/Inc
    Middlewares/ST/STM32_USB_Device_Library/Class/AUDIO/Inc
    Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Inc
    Middlewares/stm32-ssd1306-master/ssd1306
    USB_DEVICE/App
    USB_DEVICE/Target
)

target_compile_definitions(${PROJECT_NAME} PRIVATE
    USE_HAL_DRIVER
    STM32F103xE
    DEBUG                       # defined by both CubeIDE configurations
    ${VARIANT_DEFINES}
)

target_compile_options(${PROJECT_NAME} PRIVATE
    -Wall
    -ffunction-sections
    -fdata-sections
    -fstack-usage
)

target_link_options(${PROJECT_NAME} PRIVATE
    -T${LINKER_SCRIPT}
    --specs=nano.specs          # Core/Src/syscalls.c supplies the stubs
    --specs=nosys.specs
    -static
    -Wl,--gc-sections
    -Wl,-Map=${PROJECT_NAME}.map,--cref
    -Wl,--start-group -lc -lm -Wl,--end-group
    -Wl,--print-memory-usage
)

# Relink when the linker script changes.
set_target_properties(${PROJECT_NAME} PROPERTIES
    SUFFIX ".elf"
    LINK_DEPENDS ${LINKER_SCRIPT}
)

# The DFU tooling consumes the .hex (DFU/BuildDFUAutomation.py) and dfu-util
# consumes the .bin, so emit both for every build.
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:${PROJECT_NAME}>
    COMMAND ${CMAKE_OBJCOPY} -O ihex   $<TARGET_FILE:${PROJECT_NAME}> $<TARGET_FILE_DIR:${PROJECT_NAME}>/${PROJECT_NAME}.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:${PROJECT_NAME}> $<TARGET_FILE_DIR:${PROJECT_NAME}>/${PROJECT_NAME}.bin
)
