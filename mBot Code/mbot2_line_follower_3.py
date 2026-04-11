import cyberpi as cpi
import time

# -------------------------------------------------------
# mBot2 – Line follower that U-turns on white
#
# Follows black line using L1 and R1.
# If all sensors see white, does a 180 and keeps going.
# Press A to start, press A again to stop.
#
# TUNING:
#   SPEED      – drive speed (0-100)
#   TURN_SPEED – speed of the 180 turn
#   BLACK      – grayscale threshold: below = black, above = white
# -------------------------------------------------------

SPEED      = 30
TURN_SPEED = 30
BLACK      = 50

# WAIT TO START -----------------------------------------
cpi.console.println("Press A to start")
while not cpi.controller.is_press('a'):
    cpi.led.on(255, 0, 0)
while cpi.controller.is_press('a'):
    time.sleep(0.05)

cpi.led.on(0, 255, 0)
cpi.console.clear()
cpi.console.println("Following...")

# MAIN LOOP ---------------------------------------------
while True:

    if cpi.controller.is_press('a'):
        break

    L1 = cpi.quad_rgb_sensor.get_gray('l1', index=1)
    R1 = cpi.quad_rgb_sensor.get_gray('r1', index=1)

    # If both sensors see white – end of line, do a 180
    if L1 >= BLACK and R1 >= BLACK:
        cpi.mbot2.EM_stop(port="all")
        cpi.console.clear()
        cpi.console.println("White! U-turn")
        cpi.mbot2.turn(180, speed=TURN_SPEED)
        cpi.console.clear()
        cpi.console.println("Following...")

    elif L1 < BLACK and R1 < BLACK:
        # Both on black – go straight
        cpi.mbot2.drive_power(SPEED, -SPEED)

    elif L1 < BLACK:
        # Drifted right – steer left
        cpi.mbot2.drive_power(SPEED // 4, -SPEED)

    elif R1 < BLACK:
        # Drifted left – steer right
        cpi.mbot2.drive_power(SPEED, -SPEED // 4)

    time.sleep(0.02)

# STOP --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.led.off()
cpi.console.clear()
cpi.console.println("Stopped!")
