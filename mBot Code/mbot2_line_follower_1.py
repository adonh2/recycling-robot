import cyberpi as cpi
import time

# -------------------------------------------------------
# mBot2 – Line Follower with Colour Detection
#
# - Follows any non-white surface.
# - Displays the last detected colour on screen.
# - Press A to start, press A again to stop.
# -------------------------------------------------------

SPEED_NORMAL = 30

# GLOBAL VARIABLES --------------------------------------
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

def update_display():
    cpi.console.clear()
    cpi.console.println("Following line")
    cpi.console.println("Color: " + (last_color.upper() if last_color else "NONE"))

# WAIT TO START -----------------------------------------
cpi.console.println("Press A to start")
while not cpi.controller.is_press('a'):
    cpi.led.on(255, 0, 0)
while cpi.controller.is_press('a'):
    time.sleep(0.05)

cpi.led.on(0, 255, 0)
update_display()

# MAIN LOOP ---------------------------------------------
while True:

    # Stop when button A is pressed
    if cpi.controller.is_press('a'):
        break

    read_sensors()

    # --- Colour detection ---
    detected = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    if detected not in ("white", "") and detected != last_color:
        last_color = detected
        update_display()

    # --- Line following: treat anything below 50 as non-white (on the line) ---
    # drive_power(left, right): forward = positive left, negative right
    if L1 < 50 and R1 < 50:
        # Both centre sensors on line - go straight
        cpi.mbot2.drive_power(SPEED_NORMAL, -SPEED_NORMAL)

    elif L1 < 50 and R1 >= 50:
        # Only L1 on line - veer left
        cpi.mbot2.drive_power(SPEED_NORMAL // 3, -SPEED_NORMAL)

    elif R1 < 50 and L1 >= 50:
        # Only R1 on line - veer right
        cpi.mbot2.drive_power(SPEED_NORMAL, -SPEED_NORMAL // 3)

    elif L2 < 50:
        # Sharp left
        cpi.mbot2.drive_power(0, -SPEED_NORMAL)

    elif R2 < 50:
        # Sharp right
        cpi.mbot2.drive_power(SPEED_NORMAL, 0)

    else:
        # Lost the line - creep forward to reacquire
        cpi.mbot2.drive_power(SPEED_NORMAL // 2, -SPEED_NORMAL // 2)

    time.sleep(0.02)

# STOP --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.led.off()
cpi.console.clear()
cpi.console.println("Stopped!")
cpi.console.println("Last color:")
cpi.console.println(last_color.upper() if last_color else "NONE")
