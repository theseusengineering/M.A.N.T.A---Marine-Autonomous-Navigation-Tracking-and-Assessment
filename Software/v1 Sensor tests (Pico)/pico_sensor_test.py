"""Pico W sensor display and craft tilt warning prototype.

Run in Thonny with MicroPython (Raspberry Pi Pico).
Uses the Waveshare kit's SSD1327 1.5-inch display on the D1 socket.
Uses the Waveshare QMI8658C IMU on the D3 socket.
The D0 key cycles: System Armed -> active readings -> System Offline.
"""

from machine import ADC, I2C, Pin, PWM, SoftI2C
from neopixel import NeoPixel
import framebuf
import math
import time


BUS0 = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)
BUS1 = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000)
SCREEN0_BUS = SoftI2C(sda=Pin(10), scl=Pin(11), freq=400_000)
IMU_BUS = SoftI2C(sda=Pin(14), scl=Pin(15), freq=400_000)
LDR = ADC(Pin(26))
BUTTON = Pin(3, Pin.IN, Pin.PULL_UP)
BUZZER = PWM(Pin(12))
BUZZER.freq(1000)
BUZZER.duty_u16(0)
LED = NeoPixel(Pin(22, Pin.OUT), 1)
LED[0] = (0, 0, 0)
LED.write()

GREEN_LIMIT_DEG = 10.0
ALARM_LIMIT_DEG = 45.0
LED_BRIGHTNESS = 64
# The attached RGB module appears to show red for the driver's green command
# and green for its red command. Swap those channels at the output only.
LED_SWAP_RED_GREEN = True
ACCEL_LSB_PER_G = 4096.0  # QMI8658 configured for +/-8 g.
# Mean of three stationary QMI8658 readings with the assembled unit level.
# This installation has gravity along negative Z.
LEVEL_ACCEL_RAW = (-54.67, 494.33, -4022.33)
SCREEN_RETRY_MS = 5000
DISPLAY_ADDRESS = 0x3D
TEXT_ROW_HEIGHT = 16
MODE_ARMED = 0
MODE_ACTIVE = 1
MODE_OFFLINE = 2


def hex_list(addresses):
    return ", ".join("0x%02X" % address for address in addresses) or "none"


def crc8(data):
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def shtc3_read():
    BUS1.writeto(0x70, b"\x35\x17")  # Wake
    time.sleep_ms(2)
    BUS1.writeto(0x70, b"\x78\x66")  # Normal mode, temp first, no clock stretching
    time.sleep_ms(20)
    data = BUS1.readfrom(0x70, 6)
    BUS1.writeto(0x70, b"\xB0\x98")  # Sleep
    if crc8(data[0:2]) != data[2] or crc8(data[3:5]) != data[5]:
        raise ValueError("SHTC3 CRC failed")
    t_raw = (data[0] << 8) | data[1]
    rh_raw = (data[3] << 8) | data[4]
    return -45 + 175 * t_raw / 65535, 100 * rh_raw / 65535


def sgp40_raw(temp=None, humidity=None):
    if temp is None or humidity is None:
        rh_ticks, t_ticks = 0x8000, 0x6666  # Datasheet defaults, no compensation
    else:
        rh_ticks = max(0, min(65535, round(65535 * humidity / 100)))
        t_ticks = max(0, min(65535, round(65535 * (temp + 45) / 175)))
    rh_bytes = bytes((rh_ticks >> 8, rh_ticks & 0xFF))
    t_bytes = bytes((t_ticks >> 8, t_ticks & 0xFF))
    command = b"\x26\x0F" + rh_bytes + bytes((crc8(rh_bytes),)) + t_bytes + bytes((crc8(t_bytes),))
    BUS0.writeto(0x59, command)
    time.sleep_ms(40)
    data = BUS0.readfrom(0x59, 3)
    if crc8(data[0:2]) != data[2]:
        raise ValueError("SGP40 CRC failed")
    return (data[0] << 8) | data[1]


def signed16(high, low):
    value = (high << 8) | low
    return value - 65536 if value & 0x8000 else value


def qmi8658_read(address):
    # QMI8658 output is little-endian: accel XYZ followed by gyro XYZ.
    data = IMU_BUS.readfrom_mem(address, 0x35, 12)
    values = tuple(signed16(data[n + 1], data[n]) for n in range(0, 12, 2))
    return values[:3], values[3:]


def tilt_from_accel(accel):
    """Return X roll and Y pitch in degrees, relative to gravity."""
    ax, ay, az = accel
    x_angle = math.atan2(ay, az) * 180 / math.pi
    y_angle = math.atan2(-ax, math.sqrt(ay * ay + az * az)) * 180 / math.pi
    return x_angle, y_angle


def tilt_from_reference(accel, reference):
    """Angle between current and level gravity vectors, in any direction."""
    dot = sum(accel[i] * reference[i] for i in range(3))
    length = math.sqrt(sum(value * value for value in accel))
    reference_length = math.sqrt(sum(value * value for value in reference))
    if length == 0 or reference_length == 0:
        return None
    cosine = max(-1.0, min(1.0, dot / (length * reference_length)))
    return math.acos(cosine) * 180 / math.pi


def relative_angle(angle, reference_angle):
    return (angle - reference_angle + 180) % 360 - 180


def led_for_tilt(angle):
    if angle is None:
        return (0, 0, 0)
    if angle <= GREEN_LIMIT_DEG:
        return (0, LED_BRIGHTNESS, 0)
    fraction = min(1.0, (angle - GREEN_LIMIT_DEG) /
                   (ALARM_LIMIT_DEG - GREEN_LIMIT_DEG))
    return (round(LED_BRIGHTNESS * fraction),
            round(LED_BRIGHTNESS * (1 - fraction)), 0)


def led_output_color(rgb):
    return (rgb[1], rgb[0], rgb[2]) if LED_SWAP_RED_GREEN else rgb


def climate_line(temp, humidity):
    if temp is None or humidity is None:
        return "--°C --% Hum"
    line = "%.1f°C %.1f%% Hum" % (temp, humidity)
    if len(line) > 16:
        line = "%.1f°C %.0f%% Hum" % (temp, humidity)
    return line


class SSD1327:
    """Minimal SSD1327 128x128, 16-level grayscale I2C driver."""

    def __init__(self, bus, address):
        self.bus = bus
        self.address = address
        self.width = self.height = 128
        self.buffer = bytearray(self.width * self.height // 2)
        self.fb = framebuf.FrameBuffer(
            self.buffer, self.width, self.height, framebuf.GS4_HMSB)
        # SSD1327 setup used for the Waveshare 128x128 grayscale OLED.
        for command in (
                0xFD, 0x12,       # Unlock command interface
                0xAE,             # Display off
                0xA1, 0x00,       # Start line
                0xA2, 0x00,       # Display offset
                0xA0, 0x51,       # Horizontal addressing and panel remap
                0xA8, 0x7F,       # 128 multiplexed rows
                0xAB, 0x01,       # Internal VDD regulator
                0xB1, 0x51,       # Phase lengths
                0xB3, 0x01,       # Display clock
                0xBC, 0x08,       # Precharge voltage
                0xBE, 0x07,       # VCOMH
                0xB6, 0x01,       # Second precharge period
                0xD5, 0x62,       # External VSL, second precharge
                0xB9,             # Linear grayscale table
                0x81, 0x7F,       # Contrast
                0xA4,             # Normal display
                0x2E,             # Disable scrolling
                0xAF):            # Display on
            self.write_command(command)
        self.fb.fill(0)
        self.show()

    def _write(self, data):
        for attempt in range(3):
            try:
                self.bus.writeto(self.address, data)
                return
            except OSError:
                if attempt == 2:
                    raise
                time.sleep_ms(10)

    def write_command(self, command):
        self._write(bytes((0x80, command)))

    def _set_window(self, first_pixel_row, last_pixel_row):
        for command in (0x15, 0x00, 0x3F,
                        0x75, first_pixel_row, last_pixel_row):
            self.write_command(command)

    def _write_buffer(self, first_pixel_row, last_pixel_row):
        row_bytes = self.width // 2
        start = first_pixel_row * row_bytes
        end = (last_pixel_row + 1) * row_bytes
        # Send modest packets for compatibility with MicroPython SoftI2C.
        for offset in range(start, end, 64):
            self._write(b"\x40" + self.buffer[offset:min(offset + 64, end)])

    def show(self):
        self._set_window(0, self.height - 1)
        self._write_buffer(0, self.height - 1)

    def show_text_rows(self, first_row, row_count):
        first_pixel_row = first_row * TEXT_ROW_HEIGHT
        last_pixel_row = min(
            self.height - 1,
            (first_row + row_count) * TEXT_ROW_HEIGHT - 1)
        self._set_window(first_pixel_row, last_pixel_row)
        self._write_buffer(first_pixel_row, last_pixel_row)

    def draw_line(self, row, line):
        y = row * TEXT_ROW_HEIGHT
        self.fb.fill_rect(0, y, self.width, TEXT_ROW_HEIGHT, 0)
        text_y = y + 4
        for column, character in enumerate(str(line)[:16]):
            x = column * 8
            if character == "°":
                for dx, dy in ((2, 1), (3, 1), (1, 2), (4, 2),
                               (1, 3), (4, 3), (2, 4), (3, 4)):
                    self.fb.pixel(x + dx, text_y + dy, 15)
            else:
                self.fb.text(character, x, text_y, 15)

    def lines(self, text_lines):
        self.fb.fill(0)
        for row, line in enumerate(text_lines[:8]):
            self.draw_line(row, line)
        self.show()

    def update_rows(self, first_row, text_lines):
        for offset, line in enumerate(text_lines):
            self.draw_line(first_row + offset, line)
        self.show_text_rows(first_row, len(text_lines))

    def draw_large_text(self, text, y):
        """Draw the built-in 8x8 font at 2x scale, centred horizontally."""
        text = str(text)
        source_width = len(text) * 8
        source_buffer = bytearray(source_width)
        source = framebuf.FrameBuffer(
            source_buffer, source_width, 8, framebuf.MONO_HLSB)
        source.fill(0)
        source.text(text, 0, 0, 1)
        x_start = (self.width - source_width * 2) // 2
        for source_y in range(8):
            for source_x in range(source_width):
                if source.pixel(source_x, source_y):
                    self.fb.fill_rect(
                        x_start + source_x * 2, y + source_y * 2,
                        2, 2, 15)

    def status_screen(self, second_line):
        self.fb.fill(0)
        self.draw_large_text("System", 40)
        self.draw_large_text(second_line, 72)
        self.show()


def find_display(bus, found):
    for address in (DISPLAY_ADDRESS, 0x3C):
        if address in found:
            try:
                return SSD1327(bus, address)
            except Exception as exc:
                print("Display at 0x%02X did not initialise: %s" % (address, exc))
    return None


def render_mode(screen, mode, env_lines, motion_lines):
    if mode == MODE_ACTIVE:
        screen.lines(env_lines + ("", "Acc X,Y,Z (g)") + motion_lines)
    elif mode == MODE_ARMED:
        screen.status_screen("Armed")
    else:
        screen.status_screen("Offline")


print("I2C0 GP8/GP9:", hex_list(BUS0.scan()))
print("I2C1 GP6/GP7:", hex_list(BUS1.scan()))
print("Screen D1 GP10/GP11:", hex_list(SCREEN0_BUS.scan()))
print("IMU D3 GP14/GP15:", hex_list(IMU_BUS.scan()))
found0 = BUS0.scan()
found1 = BUS1.scan()
found_screen0 = SCREEN0_BUS.scan()
found_imu = IMU_BUS.scan()
print("Expected on I2C0: VOC 0x59")
print("Expected on I2C1: temp/humidity 0x70")
print("Expected on screen bus: 0x3C or 0x3D")
print("Expected on D3 IMU bus: QMI8658C 0x6B")
screen0 = find_display(SCREEN0_BUS, found_screen0)
imu_address = next((address for address in (0x6B, 0x6A) if address in found_imu), None)
if imu_address is not None:
    try:
        chip_id = IMU_BUS.readfrom_mem(imu_address, 0x00, 1)[0]
        print("IMU at 0x%02X, WHO_AM_I = 0x%02X" % (imu_address, chip_id))
        if chip_id != 0x05:
            raise ValueError("unexpected QMI8658 chip ID; check the module marking")
        IMU_BUS.writeto_mem(imu_address, 0x02, b"\x60")  # CTRL1
        IMU_BUS.writeto_mem(imu_address, 0x03, b"\x23")  # Accel: +/-8g, 1000Hz
        IMU_BUS.writeto_mem(imu_address, 0x04, b"\x53")  # Gyro: 512dps, 1000Hz
        IMU_BUS.writeto_mem(imu_address, 0x05, b"\x00")  # CTRL4
        IMU_BUS.writeto_mem(imu_address, 0x06, b"\x11")  # Accel/gyro low-pass filters
        IMU_BUS.writeto_mem(imu_address, 0x07, b"\x00")  # Motion on demand off
        IMU_BUS.writeto_mem(imu_address, 0x08, b"\x00")  # Start paused in Armed mode
        time.sleep_ms(100)
    except Exception as exc:
        print("IMU setup error:", exc)
        imu_address = None
else:
    print("QMI8658C not found on D3")

for address in found0:
    if address not in (0x59, 0x3C, 0x3D):
        print("Unidentified I2C0 device at 0x%02X" % address)

reference_accel = LEVEL_ACCEL_RAW
reference_axes = tilt_from_accel(reference_accel)
print("Level reference:", reference_accel)

env_lines = ("--°C --% Hum", "VOC raw: --", "LDR raw: --")
motion_lines = ("--,--,--", "X tilt: --°", "Y tilt: --°")
tilt_line = "Tilt: --°"
status_line = "State: NO IMU"
mode = MODE_ARMED
if screen0:
    try:
        render_mode(screen0, mode, env_lines, motion_lines)
    except OSError as exc:
        print("Initial screen write failed:", exc)
        screen0 = None
next_screen_retry_ms = time.ticks_add(time.ticks_ms(), SCREEN_RETRY_MS)

next_env_ms = time.ticks_ms()
frames_since_env = 0
last_accel = last_gyro = filtered_accel = None
last_filter_ms = time.ticks_ms()
last_color = None
last_beep_on = False
alarm_started_ms = None
button_raw = button_stable = BUTTON.value()
button_change_ms = time.ticks_ms()

try:
    while True:
        now = time.ticks_ms()
        if screen0 is None and time.ticks_diff(now, next_screen_retry_ms) >= 0:
            next_screen_retry_ms = time.ticks_add(now, SCREEN_RETRY_MS)
            try:
                found_screen0 = SCREEN0_BUS.scan()
                screen0 = find_display(SCREEN0_BUS, found_screen0)
                if screen0:
                    render_mode(screen0, mode, env_lines, motion_lines)
                    print("Screen reconnected at 0x%02X" % screen0.address)
                else:
                    print("Screen not found; scan:", hex_list(found_screen0))
            except OSError as exc:
                print("Screen reconnect failed:", exc)
                screen0 = None
        if mode == MODE_ACTIVE and time.ticks_diff(now, next_env_ms) >= 0:
            # One environmental reading per second; skip missed intervals.
            next_env_ms = time.ticks_add(next_env_ms, 1000)
            if time.ticks_diff(now, next_env_ms) >= 0:
                next_env_ms = time.ticks_add(now, 1000)

            temp = humidity = raw = None
            if 0x70 in found1:
                try:
                    temp, humidity = shtc3_read()
                    print("Temp %.2f C | humidity %.1f %%" % (temp, humidity))
                except Exception as exc:
                    print("Temp/humidity read error:", exc)
            else:
                print("Temp/humidity SHTC3 not found")

            if 0x59 in found0:
                try:
                    raw = sgp40_raw(temp, humidity)
                    print("VOC SGP40 raw SRAW:", raw, "(not a VOC index or ppm)")
                except Exception as exc:
                    print("VOC read error:", exc)
            else:
                print("VOC SGP40 not found")

            adc_value = LDR.read_u16()
            env_lines = (
                climate_line(temp, humidity),
                "VOC raw: " + (str(raw) if raw is not None else "missing"),
                "LDR raw: %d" % adc_value,
            )
            print("LDR ADC:", adc_value, "of 65535")
            if last_accel is not None:
                print("QMI8658 accel XYZ raw:", last_accel,
                      "| gyro XYZ raw:", last_gyro)
                if filtered_accel is not None:
                    log_x, log_y = tilt_from_accel(filtered_accel)
                    print("Tilt from level: %.1f deg | X %.1f deg | Y %.1f deg" % (
                        tilt_from_reference(filtered_accel, reference_accel),
                        relative_angle(log_x, reference_axes[0]),
                        relative_angle(log_y, reference_axes[1])))
            print("IMU display updates in previous second:", frames_since_env)
            frames_since_env = 0
            if screen0:
                try:
                    screen0.update_rows(0, env_lines)
                except Exception as exc:
                    print("Screen write error:", exc)
                    screen0 = None

        if mode == MODE_ACTIVE and imu_address is not None:
            try:
                last_accel, last_gyro = qmi8658_read(imu_address)
            except Exception as exc:
                print("IMU read error:", exc)
                last_accel = last_gyro = None
                time.sleep_ms(50)

        if mode == MODE_ACTIVE and last_accel is not None:
            sample_ms = time.ticks_ms()
            if filtered_accel is None:
                filtered_accel = tuple(last_accel)
            else:
                elapsed_ms = max(0, time.ticks_diff(sample_ms, last_filter_ms))
                alpha = elapsed_ms / (150 + elapsed_ms)
                filtered_accel = tuple(
                    filtered_accel[i] + alpha * (last_accel[i] - filtered_accel[i])
                    for i in range(3)
                )
            last_filter_ms = sample_ms

        angle = None
        if mode == MODE_ACTIVE and last_accel is not None:
            angle = tilt_from_reference(filtered_accel, reference_accel)
            acceleration = tuple(value / ACCEL_LSB_PER_G for value in filtered_accel)
            x_angle, y_angle = tilt_from_accel(filtered_accel)
            motion_lines = (
                "%.1f,%.1f,%.1f" % acceleration,
                "X tilt: %.1f°" % relative_angle(x_angle, reference_axes[0]),
                "Y tilt: %.1f°" % relative_angle(y_angle, reference_axes[1]),
            )
            tilt_line = "Tilt: %.1f°" % angle
            if angle <= GREEN_LIMIT_DEG:
                status_line = "State: LEVEL"
            elif angle <= ALARM_LIMIT_DEG:
                status_line = "State: CAUTION"
            else:
                status_line = "State: ALARM"
        else:
            motion_lines = ("missing", "X tilt: --°", "Y tilt: --°")
            tilt_line = "Tilt: --°"
            status_line = "State: NO IMU"
        color = led_for_tilt(angle)
        if color != last_color:
            LED[0] = led_output_color(color)
            LED.write()
            print("LED logical RGB:", color,
                  "| driver tuple:", led_output_color(color))
            last_color = color

        if angle is not None and angle > ALARM_LIMIT_DEG:
            if alarm_started_ms is None:
                alarm_started_ms = now
            beep_on = time.ticks_diff(now, alarm_started_ms) % 500 < 150
        else:
            alarm_started_ms = None
            beep_on = False
        if beep_on != last_beep_on:
            BUZZER.duty_u16(18000 if beep_on else 0)
            last_beep_on = beep_on

        if screen0 and mode == MODE_ACTIVE:
            try:
                screen0.update_rows(5, motion_lines)
                frames_since_env += 1
            except Exception as exc:
                print("Screen write error:", exc)
                screen0 = None

        # Each debounced press advances Armed -> Active -> Offline -> Armed.
        now = time.ticks_ms()
        raw = BUTTON.value()
        if raw != button_raw:
            button_raw = raw
            button_change_ms = now
        if raw != button_stable and time.ticks_diff(now, button_change_ms) >= 30:
            button_stable = raw
            if raw == 0:
                mode = (mode + 1) % 3
                last_accel = last_gyro = filtered_accel = None
                alarm_started_ms = None
                frames_since_env = 0
                next_env_ms = now
                mode_name = ("ARMED", "ACTIVE", "OFFLINE")[mode]
                print("System mode:", mode_name)
                if imu_address is not None:
                    try:
                        enabled = b"\x03" if mode == MODE_ACTIVE else b"\x00"
                        IMU_BUS.writeto_mem(imu_address, 0x08, enabled)
                    except Exception as exc:
                        print("IMU mode change error:", exc)
                if screen0:
                    try:
                        render_mode(screen0, mode, env_lines, motion_lines)
                    except Exception as exc:
                        print("Screen write error:", exc)
                        screen0 = None

        if mode != MODE_ACTIVE or imu_address is None or screen0 is None:
            time.sleep_ms(50)
finally:
    BUZZER.duty_u16(0)
    LED[0] = (0, 0, 0)
    LED.write()
