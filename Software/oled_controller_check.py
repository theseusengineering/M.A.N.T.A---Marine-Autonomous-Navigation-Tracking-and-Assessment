"""Static SH1106 COM-layout comparison for the two wired 1.3-inch displays.

Run once in Thonny. Both screens use SH1106 page addressing.
Left/screen 1 (GP16/17) uses alternative COM layout (0x12).
Right/screen 2 (GP14/15) uses sequential COM layout (0x02).
Each fills all eight 8-pixel text rows and then stops; no sensor updates are involved.
"""

from machine import Pin, SoftI2C
import framebuf


left_bus = SoftI2C(sda=Pin(16), scl=Pin(17), freq=100_000)
right_bus = SoftI2C(sda=Pin(14), scl=Pin(15), freq=100_000)


def address(bus):
    found = bus.scan()
    print("I2C scan:", [hex(value) for value in found])
    for candidate in (0x3C, 0x3D):
        if candidate in found:
            return candidate
    raise RuntimeError("OLED not found at 0x3C or 0x3D")


def command(bus, addr, value):
    bus.writeto(addr, bytes((0x00, value)))


def data_chunks(bus, addr, data):
    for start in range(0, len(data), 16):
        bus.writeto(addr, b"\x40" + data[start:start + 16])


def pattern(title):
    buffer = bytearray(1024)
    fb = framebuf.FrameBuffer(buffer, 128, 64, framebuf.MONO_VLSB)
    fb.fill(0)
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for row_number in range(8):
        prefix = "%s%d" % (title, row_number)
        shifted = letters[row_number * 3:] + letters[:row_number * 3]
        text = (prefix + shifted)[:16]
        fb.text(text, 0, row_number * 8, 1)
    return buffer


def test_sh1106(bus, addr, com_config, title):
    setup = (0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00,
             0x40, 0xAD, 0x8B, 0xA0, 0xC0, 0xDA, com_config,
             0x81, 0x7F, 0xD9, 0x22, 0xDB, 0x35, 0xA4,
             0xA6, 0xAF)
    for value in setup:
        command(bus, addr, value)
    buffer = pattern(title)
    for page in range(8):
        for value in (0xB0 | page, 0x02, 0x10):
            command(bus, addr, value)
        data_chunks(bus, addr, buffer[page * 128:(page + 1) * 128])


print("Left screen: SH1106 alternative COM layout")
left_addr = address(left_bus)
test_sh1106(left_bus, left_addr, 0x12, "ALT")

print("Right screen: SH1106 sequential COM layout")
right_addr = address(right_bus)
test_sh1106(right_bus, right_addr, 0x02, "SEQ")

print("Done. Displays remain static for inspection.")
