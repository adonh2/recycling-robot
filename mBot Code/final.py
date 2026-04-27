import cyberpi as cpi
import time

# -------------------------------------------------------
# mBot2 - Junction navigation
#
# A = start the run
# B = restart (back to Press A screen at any time)
#
# 1. Follow black line until input colour detected
# 2. Turn:  red or green → 90° anticlockwise
#           blue or purple → 90° clockwise
# 3. Drive forward until any sensor detects black
# 4. Follow branch until input colour detected
# -------------------------------------------------------

input = "red"

SPEED      = 30
TURN_SPEED = 30

green  = (0, 255, 0)
red    = (255, 0, 0)
blue   = (0, 0, 255)
off    = (0, 0, 0)
purple = (128, 0, 128)
yellow = (255, 255, 0)

# FUNCTIONS ---------------------------------------------
def led(color):
    cpi.led.on(color[0], color[1], color[2])

def color_to_rgb(name):
    if name == "red":    return red
    if name == "green":  return green
    if name == "blue":   return blue
    if name == "purple": return purple
    if name == "yellow": return yellow
    return off

def b_pressed():
    """True if B is pressed - signals a restart."""
    if cpi.controller.is_press('b'):
        cpi.mbot2.EM_stop(port="all")
        led(off)
        return True
    return False

def any_sensor_black():
    for probe in ('l2', 'l1', 'r1', 'r2'):
        if cpi.quad_rgb_sensor.get_color_sta(probe, index=1) == "black":
            return True
    return False

def follow_step():
    """One step of line following. Returns L1 and R1 colour names."""
    l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)
    L1 = l1_color != "white"
    R1 = r1_color != "white"

    if L1 and R1:
        cpi.mbot2.drive_power(SPEED, -SPEED)
    elif L1:
        cpi.mbot2.drive_power(SPEED // 4, -SPEED)
    elif R1:
        cpi.mbot2.drive_power(SPEED, -SPEED // 4)
    else:
        cpi.mbot2.drive_power(SPEED // 2, -SPEED // 2)

    return l1_color, r1_color

# OUTER LOOP - B always brings us back here -------------
while True:

    # WAIT TO START -------------------------------------
    cpi.console.clear()
    cpi.console.println("Target: " + input)
    cpi.console.println("Press A to start")
    while not cpi.controller.is_press('a'):
        led(red)
    while cpi.controller.is_press('a'):
        time.sleep(0.05)
    led(off)

    restart = False

    # PHASE 1: Follow until input colour ----------------
    cpi.console.clear()
    cpi.console.println("Going to junction")
    while True:
        if b_pressed():
            restart = True
            break
        l1_color, r1_color = follow_step()
        if l1_color == input or r1_color == input:
            cpi.mbot2.EM_stop(port="all")
            led(color_to_rgb(input))
            time.sleep(0.5)
            break
        time.sleep(0.02)
    if restart: continue

    # PHASE 2: Turn -------------------------------------
    cpi.console.clear()
    cpi.console.println("Turning")
    if input in ("red", "green"):
        cpi.mbot2.turn(-90, speed=TURN_SPEED)
    elif input in ("blue", "purple"):
        cpi.mbot2.turn(90, speed=TURN_SPEED)
    led(off)
    if b_pressed():
        continue

    # PHASE 3: Drive until black ------------------------
    cpi.console.clear()
    cpi.console.println("Finding branch")
    while True:
        if b_pressed():
            restart = True
            break
        cpi.mbot2.drive_power(SPEED, -SPEED)
        if any_sensor_black():
            cpi.mbot2.EM_stop(port="all")
            break
        time.sleep(0.02)
    if restart: continue

    # PHASE 4: Follow branch until input colour ---------
    cpi.console.clear()
    cpi.console.println("Following branch")
    while True:
        if b_pressed():
            restart = True
            break
        l1_color, r1_color = follow_step()
        if l1_color == input or r1_color == input:
            cpi.mbot2.EM_stop(port="all")
            led(color_to_rgb(input))
            cpi.console.clear()
            cpi.console.println("Arrived!")
            cpi.console.println("Press B to reset")
            break
        time.sleep(0.02)
    if restart: continue

    # WAIT FOR B AFTER ARRIVAL --------------------------
    while not cpi.controller.is_press('b'):
        time.sleep(0.05)
    while cpi.controller.is_press('b'):
        time.sleep(0.05)
    led(off)