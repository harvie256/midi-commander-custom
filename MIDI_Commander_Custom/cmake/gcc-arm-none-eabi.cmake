#
# Toolchain file for the bare-metal Cortex-M3 (STM32F103RET) target.
#
# Override the compiler location with -DTOOLCHAIN_PREFIX=/path/to/gcc-arm/bin/
# if you do not want the arm-none-eabi-gcc that is on PATH.
#

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(TOOLCHAIN_PREFIX "" CACHE STRING "Directory holding arm-none-eabi-*, with trailing slash")

set(CMAKE_C_COMPILER   ${TOOLCHAIN_PREFIX}arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER})
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_PREFIX}arm-none-eabi-g++)
set(CMAKE_OBJCOPY      ${TOOLCHAIN_PREFIX}arm-none-eabi-objcopy)
set(CMAKE_SIZE         ${TOOLCHAIN_PREFIX}arm-none-eabi-size)

# The compiler cannot link a hosted test binary, so only ask it to build one.
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# Cortex-M3 has no FPU, so the soft float ABI is the only option.
set(TARGET_FLAGS "-mcpu=cortex-m3 -mthumb -mfloat-abi=soft")

set(CMAKE_C_FLAGS_INIT   "${TARGET_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT "${TARGET_FLAGS}")
set(CMAKE_ASM_FLAGS_INIT "${TARGET_FLAGS} -x assembler-with-cpp")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
