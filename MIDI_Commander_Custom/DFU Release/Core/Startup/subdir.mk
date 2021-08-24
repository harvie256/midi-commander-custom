################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (9-2020-q2-update)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
S_SRCS += \
../Core/Startup/startup_stm32f103retx.s 

OBJS += \
./Core/Startup/startup_stm32f103retx.o 

S_DEPS += \
./Core/Startup/startup_stm32f103retx.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Startup/%.o: ../Core/Startup/%.s Core/Startup/subdir.mk
	arm-none-eabi-gcc -mcpu=cortex-m3 -g3 -c -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/stm32-ssd1306-master/ssd1306" -I"D:/midi-commander-custom/MIDI_Commander_Custom/Middlewares/ST/STM32_USB_Device_Library/Class/MIDI/Inc" -x assembler-with-cpp -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@" "$<"

