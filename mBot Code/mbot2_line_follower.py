import cyberpi as cpi
import time

# -------------------------------------------------------
# mBot2 – Line Follower with Colour Detection
#
# - Follows a black line on a white background.
# - Detects colour markers on the line and reacts:
#       RED    → stop for 1 second
#       BLUE   → turn around (180°)
#       GREEN  → speed boost for 2 seconds
#       YELLOW → beep and continue
# - Press A to start, press A again to stop.
# - Current action and last colour shown on screen.
# -------------------------------------------------------

# SPEEDS ------------------------------------------------
SPEED_NORMAL = 30   # normal line following speed
SPEED_BOOST  = 55   # green marker boost speed
SPEED_TURN   = 30   # turning speed
BOOST_TIME   = 2.0  # seconds to boost after green marker

# GLOBAL SENSOR VALUES ----------------------------------
L2 = 0
L1 = 0
R1 = 0
R2 = 0
last_color = ""

# FUNCTIONS ---------------------------------------------
def read_sensors():
    global L2, L1, R1, R2
    L2 = cpi.quad_rgb_sensor.get_gray('l2', index=1)
    L1 = cpi.quad_rgb_sensor.get_gray('l1', index=1)
    R1 = cpi.quad_rgb_sensor.get_gray('r1', index=1)
    R2 = cpi.quad_rgb_sensor.get_gray('r2', index=1)

def get_color():
    return cpi.quad_rgb_sensor.get_color_sta('l1', index=1)

def update_display(action):
    cpi.console.clear()
    cpi.console.println("Action: " + action)
    cpi.console.println("Color:  " + (last_color.upper() if last_color else "NONE"))

def handle_color(color):
    """React to a detected colour marker."""
    global last_color
    if color in ("red", "green", "blue", "yellow", "cyan", "purple"):
        if color != last_color:
            last_color = color

        if color == "red":
            # Stop for 1 second
            cpi.mbot2.EM_stop(port="all")
            cpi.led.on(255, 0, 0)
            update_display("STOP (red)")
            time.sleep(1)
            cpi.led.on(0, 255, 0)
            return "normal"

        elif color == "blue":
            # Turn around 180 degrees
            cpi.led.on(0, 0, 255)
            update_display("U-TURN (blue)")
            cpi.mbot2.turn(180, speed=SPEED_TURN)
            cpi.led.on(0, 255, 0)
            return "normal"

        elif color == "green":
            # Speed boost
            cpi.led.on(0, 255, 0)
            update_display("BOOST (green)")
            return "boost"

        elif color == "yellow":
            # Beep and continue
            cpi.led.on(255, 220, 0)
            update_display("BEEP (yellow)")
            cpi.audio.play('beeps')
            cpi.led.on(0, 255, 0)
            return "normal"

        elif color == "cyan":
            cpi.led.on(0, 220, 220)
            update_display("CYAN marker")
            cpi.led.on(0, 255, 0)
            return "normal"

        elif color == "purple":
            cpi.led.on(160, 0, 200)
            update_display("PURPLE marker")
            cpi.led.on(0, 255, 0)
            return "normal"

    return None  # no special colour detected

# WAIT TO START -----------------------------------------
cpi.console.println("Press A")
cpi.console.println("to start")
while not cpi.controller.is_press('a'):
    cpi.led.on(255, 0, 0)
while cpi.controller.is_press('a'):
    time.sleep(0.05)

cpi.led.on(0, 255, 0)
update_display("FOLLOWING")

# MAIN LOOP ---------------------------------------------
mode = "normal"          # "normal" or "boost"
boost_timer = 0.0

while True:

    # Stop when button A is pressed
    if cpi.controller.is_press('a'):
        break

    read_sensors()

    # --- Colour detection ---
    detected = get_color()
    if detected not in ("white", "black", ""):
        result = handle_color(detected)
        if result is not None:
            mode = result
            if mode == "boost":
                boost_timer = time.time() + BOOST_TIME

    # --- Return to normal after boost expires ---
    if mode == "boost" and time.time() > boost_timer:
        mode = "normal"
        update_display("FOLLOWING")
        cpi.led.on(0, 255, 0)

    # --- Choose speed based on mode ---
    spd = SPEED_BOOST if mode == "boost" else SPEED_NORMAL

    # --- Line following logic (L1/R1 primary, L2/R2 for sharp bends) ---
    # drive_power(left, right): forward = positive left, negative right
    if L1 < 50 and R1 < 50:
        # Both centre sensors on line – go straight
        cpi.mbot2.drive_power(spd, -spd)

    elif L1 < 50 and R1 >= 50:
        # Only L1 on line – veer left
        cpi.mbot2.drive_power(spd // 3, -spd)

    elif R1 < 50 and L1 >= 50:
        # Only R1 on line – veer right
        cpi.mbot2.drive_power(spd, -spd // 3)

    elif L2 < 50:
        # Sharp left – outer sensor picks up line
        cpi.mbot2.drive_power(0, -spd)

    elif R2 < 50:
        # Sharp right – outer sensor picks up line
        cpi.mbot2.drive_power(spd, 0)

    else:
        # Lost the line – slow forward to try to reacquire
        cpi.mbot2.drive_power(spd // 2, -spd // 2)

    time.sleep(0.02)

# STOP --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.led.off()
cpi.console.clear()
cpi.console.println("Stopped!")
cpi.console.println("Last color:")
cpi.console.println(last_color.upper() if last_color else "NONE")
