"""Brief SH1106 all-pixels-on test, independent of the frame buffer.

Run in Thonny and photograph both screens while they are uniformly lit.
The test restores normal display mode and blanks both screens after 20 seconds.
"""

from machine import Pin, SoftI2C
import time


SCREENS = (
    ("left GP16/17", SoftI2C(sda=Pin(16), scl=Pin(17), freq=100_000)),
    ("right GP14/15", SoftI2C(sda=Pin(14), scl=Pin(15), freq=100_000)),
)


def command(bus, addr, value):
    bus.writeto(addr, bytes((0x00, value)))


def clear(bus, addr):
    for page in range(8):
        for value in (0xB0 | page, 0x02, 0x10):
            command(bus, addr, value)
        for _ in range(8):
            bus.writeto(addr, b"\x40" + bytes(16))


found_screens = []
for name, bus in SCREENS:
    found = bus.scan()
    print(name, "I2C scan:", [hex(value) for value in found])
    addr = next((value for value in (0x3C, 0x3D) if value in found), None)
    if addr is None:
        raise RuntimeError("OLED not found on " + name)
    # Alternative COM layout was the clearer of the two layouts in the text test.
    for value in (0xAE, 0xA8, 0x3F, 0xD3, 0x00, 0x40,
                  0xA0, 0xC0, 0xDA, 0x12, 0x81, 0x40, 0xA6, 0xAF):
        command(bus, addr, value)
    found_screens.append((name, bus, addr))

try:
    for name, bus, addr in found_screens:
        command(bus, addr, 0xA5)  # Illuminate every pixel regardless of display RAM.
    print("All pixels ON for 20 seconds. Check both screens now.")
    time.sleep(20)
finally:
    for name, bus, addr in found_screens:
        command(bus, addr, 0xA4)  # Return to normal display RAM mode.
        clear(bus, addr)
    print("Normal mode restored; both screens blanked.")
