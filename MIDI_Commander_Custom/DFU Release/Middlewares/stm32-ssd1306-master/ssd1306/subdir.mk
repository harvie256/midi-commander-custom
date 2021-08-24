################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (9-2020-q2-update)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/stm32-ssd1306-master/ssd1306/ssd1306.c \
../Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_fonts.c \
../Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_tests.c 

OBJS += \
./Middlewares/stm32-ssd1306-master/ssd1306/ssd1306.o \
./Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_fonts.o \
./Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_tests.o 

C_DEPS += \
./Middlewares/stm32-ssd1306-master/ssd1306/ssd1306.d \
./Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_fonts.d \
./Middlewares/stm32-ssd1306-master/ssd1306/ssd1306_tests.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/stm32-ssd1306-master/ssd1306/%.o: ../Middlewares/stm32-ssd1306-master/ssd1306/%.c Middlewares/stm32-ssd1306-master/ssd1306/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DUSE_HAL_DRIVER -DUSER_VECT_TAB_ADDRESS -DSTM32F103xE -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/stm32-ssd1306-master/ssd1306" -I../USB_DEVICE/App -I../USB_DEVICE/Target -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/AUDIO/Inc -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Inc" -O2 -ffunction-sections -fdata-sections -Wall -fstack-usage -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

