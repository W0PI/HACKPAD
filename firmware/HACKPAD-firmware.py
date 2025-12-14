import time
import board
import busio
import adafruit_ssd1306

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.rgb import RGB, PixelPin

# =====================
# Keyboard init
# =====================
keyboard = KMKKeyboard()

# =====================
# KEYS (5)
# =====================
keyboard.matrix = KeysScanner(
    pins=[
        board.GP28,
        board.GP29,
        board.GP6,
        board.GP7,
        board.GP0,
    ],
    value_when_pressed=False,
)

keyboard.keymap = [
    [KC.A, KC.B, KC.C, KC.D, KC.ENT]
]

# =====================
# OLED (SSD1306 framebuffer)
# =====================
i2c = busio.I2C(scl=board.GP27, sda=board.GP26)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

def oled_show_mode(text):
    oled.fill(0)
    oled.text(text, 0, 0, 1)  # LEFT side
    oled.show()

# =====================
# RGB LEDs
# =====================
rgb = RGB(
    pixel_pin=PixelPin(board.GP1),
    num_pixels=10,          # change if needed
    brightness_default=0.3,
)
keyboard.modules.append(rgb)

# =====================
# ROTARY ENCODER LOGIC
# =====================
ENC_A = board.GP3
ENC_B = board.GP4
ENC_SW = board.GP2

scroll_mode = False
press_times = []
hold_start = None

oled_show_mode("VOLUME")

def handle_encoder():
    global scroll_mode, press_times, hold_start

    # --- Encoder button ---
    if not ENC_SW.value:  # pressed (active low)
        if hold_start is None:
            hold_start = time.monotonic()
        elif time.monotonic() - hold_start >= 3:
            scroll_mode = not scroll_mode
            oled_show_mode("SCROLL" if scroll_mode else "VOLUME")
            hold_start = None
            press_times.clear()
            time.sleep(0.5)
            return
    else:
        if hold_start:
            press_times.append(time.monotonic())
        hold_start = None

    # --- Handle multi-press ---
    press_times[:] = [t for t in press_times if time.monotonic() - t < 0.5]
    if len(press_times) == 1:
        keyboard.send(KC.MPLY)
        press_times.clear()
    elif len(press_times) == 2:
        keyboard.send(KC.MNXT)
        press_times.clear()
    elif len(press_times) == 3:
        keyboard.send(KC.MPRV)
        press_times.clear()

# =====================
# ENCODER ROTATION
# =====================
last_a = True

def scan_encoder():
    global last_a
    a = ENC_A.value
    b = ENC_B.value

    if a != last_a:
        if not a:
            if b:
                keyboard.send(KC.UP if scroll_mode else KC.VOLU)
            else:
                keyboard.send(KC.DOWN if scroll_mode else KC.VOLD)
        last_a = a

# =====================
# Main loop hook
# =====================
def before_matrix_scan(keyboard):
    scan_encoder()
    handle_encoder()

keyboard.before_matrix_scan = before_matrix_scan

# =====================
# START
# =====================
if __name__ == "__main__":
    keyboard.go()
