################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (9-2020-q2-update)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../USB_DEVICE/App/usb_device.c \
../USB_DEVICE/App/usbd_audio_if.c \
../USB_DEVICE/App/usbd_desc.c \
../USB_DEVICE/App/usbd_midi_if.c 

OBJS += \
./USB_DEVICE/App/usb_device.o \
./USB_DEVICE/App/usbd_audio_if.o \
./USB_DEVICE/App/usbd_desc.o \
./USB_DEVICE/App/usbd_midi_if.o 

C_DEPS += \
./USB_DEVICE/App/usb_device.d \
./USB_DEVICE/App/usbd_audio_if.d \
./USB_DEVICE/App/usbd_desc.d \
./USB_DEVICE/App/usbd_midi_if.d 


# Each subdirectory must supply rules for building sources it contributes
USB_DEVICE/App/usb_device.o: ../USB_DEVICE/App/usb_device.c USB_DEVICE/App/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DUSE_HAL_DRIVER -DUSER_VECT_TAB_ADDRESS -DSTM32F103xE -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/stm32-ssd1306-master/ssd1306" -I../USB_DEVICE/App -I../USB_DEVICE/Target -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/AUDIO/Inc -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Inc" -O2 -ffunction-sections -fdata-sections -Wall -fstack-usage -MMD -MP -MF"USB_DEVICE/App/usb_device.d" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"
USB_DEVICE/App/usbd_audio_if.o: ../USB_DEVICE/App/usbd_audio_if.c USB_DEVICE/App/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DUSE_HAL_DRIVER -DUSER_VECT_TAB_ADDRESS -DSTM32F103xE -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/stm32-ssd1306-master/ssd1306" -I../USB_DEVICE/App -I../USB_DEVICE/Target -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/AUDIO/Inc -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Inc" -O2 -ffunction-sections -fdata-sections -Wall -fstack-usage -MMD -MP -MF"USB_DEVICE/App/usbd_audio_if.d" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"
USB_DEVICE/App/usbd_desc.o: ../USB_DEVICE/App/usbd_desc.c USB_DEVICE/App/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DUSE_HAL_DRIVER -DUSER_VECT_TAB_ADDRESS -DSTM32F103xE -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/stm32-ssd1306-master/ssd1306" -I../USB_DEVICE/App -I../USB_DEVICE/Target -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/AUDIO/Inc -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Inc" -O2 -ffunction-sections -fdata-sections -Wall -fstack-usage -MMD -MP -MF"USB_DEVICE/App/usbd_desc.d" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"
USB_DEVICE/App/usbd_midi_if.o: ../USB_DEVICE/App/usbd_midi_if.c USB_DEVICE/App/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DUSE_HAL_DRIVER -DUSER_VECT_TAB_ADDRESS -DSTM32F103xE -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/stm32-ssd1306-master/ssd1306" -I../USB_DEVICE/App -I../USB_DEVICE/Target -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/AUDIO/Inc -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Inc" -O2 -ffunction-sections -fdata-sections -Wall -fstack-usage -MMD -MP -MF"USB_DEVICE/App/usbd_midi_if.d" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"
