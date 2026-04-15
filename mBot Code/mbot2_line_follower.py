import cyberpi as cpi
import time

# -------------------------------------------------------
# mBot2 – Line follower using colour detection only
#
# Follows black line using L1 and R1.
# White = end of line, does a 180 and keeps going.
# Any other colour (red, green, blue etc) = treated as black.
# Press A to start, press A again to stop.
#
# TUNING:
#   SPEED      – drive speed (0-100)
#   TURN_SPEED – speed of the 180 turn
# -------------------------------------------------------

SPEED      = 30
TURN_SPEED = 30

def on_line(probe):
    """Returns True if the probe is on anything other than white."""
    color = cpi.quad_rgb_sensor.get_color_sta(probe, index=1)
    return color != "white"

# WAIT TO START -----------------------------------------
cpi.console.println("Press A to start")
while not cpi.controller.is_press('a'):
    cpi.led.on(0, 0, 0)
while cpi.controller.is_press('a'):
    time.sleep(0.05)

cpi.led.on(0, 0, 0)
cpi.console.clear()
cpi.console.println("Following...")

# MAIN LOOP ---------------------------------------------
while True:

    if cpi.controller.is_press('a'):
        break

    L1 = on_line('l1')
    R1 = on_line('r1')

    # Both sensors see white – end of line, do a 180
    if not L1 and not R1:
        cpi.mbot2.EM_stop(port="all")
        cpi.console.clear()
        cpi.console.println("White! U-turn")
        cpi.mbot2.turn(180, speed=TURN_SPEED)
        cpi.console.clear()
        cpi.console.println("Following...")

    elif L1 and R1:
        # Both on line – go straight
        cpi.mbot2.drive_power(SPEED, -SPEED)

    elif L1:
        # Drifted right – steer left
        cpi.mbot2.drive_power(SPEED // 4, -SPEED)

    elif R1:
        # Drifted left – steer right
        cpi.mbot2.drive_power(SPEED, -SPEED // 4)

    time.sleep(0.02)

# STOP --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.led.off()
cpi.console.clear()
cpi.console.println("Stopped!")
