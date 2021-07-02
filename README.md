# midi-commander-custom
Custom Firmware for the MeloAudio Midi Commander

There's no intention of this replacing the default firmware functions. I'm creating this purely for custom requirements that the original firmware will never fulfill.

Current Status:
- Hardware is nutted out as far as I need. I haven't bothered with the expression pedals or battery charging, but I'm sure they're not complicated.
- It's pretty simple, an STM32F103RET with LEDs, buttons, an SSD1306 display, UART midi interface, usb connector and that's about it.

Things that need to be done:
- High Priority stuff
~~1. Work out the DFU setup.  Currently I'm just programming with an STlink, but for this to be really useful download over the DFU interface needs to be sorted.~~
~~2. Work out the USB-MIDI firmware.  There's a few examples online of people replacing the USB descriptors files of the USB-VCP to create a MIDI device.  Shouldn't be too hard.~~

With the first stuff done, time to make an application out of it!

- Mid priority
3. Create at least a basic menu system.
