import cyberpi as cpi
import time

SPEED      = 30
TURN_SPEED = 30

last_turn_time = 0

def on_line(probe):
    color = cpi.quad_rgb_sensor.get_color_sta(probe, index=1)
    return color != "white"

# WAIT TO START -----------------------------------------
cpi.console.println("Press A to start")
while not cpi.controller.is_press('a'):
    pass
while cpi.controller.is_press('a'):
    time.sleep(0.05)

cpi.console.clear()
cpi.console.println("Following...")

# MAIN LOOP ---------------------------------------------
while True:

    if cpi.controller.is_press('a'):
        break

    l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)

    L1 = on_line('l1')
    R1 = on_line('r1')

    # Red detected – stop and turn left
    if (l1_color == "red" or r1_color == "red") and (time.time() - last_turn_time > 2):
        cpi.mbot2.EM_stop(port="all")
        cpi.console.clear()
        cpi.console.println("Red! Turning left")
        cpi.mbot2.turn_left(speed=TURN_SPEED, run_time=1)
        cpi.console.clear()
        cpi.console.println("Following...")
        last_turn_time = time.time()

    # White – U-turn
    elif not L1 and not R1:
        cpi.mbot2.EM_stop(port="all")
        cpi.console.clear()
        cpi.console.println("White! U-turn")
        cpi.mbot2.turn(180, speed=TURN_SPEED)
        cpi.console.clear()
        cpi.console.println("Following...")

    elif L1 and R1:
        cpi.mbot2.drive_power(SPEED, -SPEED)

    elif L1:
        cpi.mbot2.drive_power(SPEED // 4, -SPEED)

    elif R1:
        cpi.mbot2.drive_power(SPEED, -SPEED // 4)

    time.sleep(0.02)

# STOP --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.console.clear()
cpi.console.println("Stopped!")
