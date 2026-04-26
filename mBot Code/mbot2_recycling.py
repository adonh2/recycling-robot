import cyberpi as cpi
import time

# -------------------------------------------------------
# mBot2 - Recycling delivery
#
# Drives along the black line from yellow start, stops just
# past the patch matching `target`, waits for "deposit",
# then U-turns and returns to yellow.
# -------------------------------------------------------

target = "red"   # change to: "red", "blue", "green", "purple"

SPEED        = 25
TURN_SPEED   = 30
OVERSHOOT    = 0.4   # seconds to drive past the colour patch
DEPOSIT_TIME = 3.0   # seconds to "deposit" (just a wait for now)

# COLOUR HELPERS ----------------------------------------
green_led  = (0, 255, 0)
red_led    = (255, 0, 0)
blue_led   = (0, 0, 255)
purple_led = (128, 0, 128)
yellow_led = (255, 255, 0)
off_led    = (0, 0, 0)

def led(color):
    cpi.led.on(color[0], color[1], color[2])

def color_to_led(name):
    if name == "red":    return red_led
    if name == "green":  return green_led
    if name == "blue":   return blue_led
    if name == "purple": return purple_led
    if name == "yellow": return yellow_led
    return off_led

def on_line(probe):
    """Returns True if the probe sees anything that isn't white."""
    color = cpi.quad_rgb_sensor.get_color_sta(probe, index=1)
    return color != "white"

def follow_step():
    """One step of line-following using L1/R1."""
    L1 = on_line('l1')
    R1 = on_line('r1')

    if L1 and R1:
        cpi.mbot2.drive_power(SPEED, -SPEED)
    elif L1:
        cpi.mbot2.drive_power(SPEED // 4, -SPEED)
    elif R1:
        cpi.mbot2.drive_power(SPEED, -SPEED // 4)
    else:
        # Lost line - creep forward
        cpi.mbot2.drive_power(SPEED // 2, -SPEED // 2)

# WAIT TO START -----------------------------------------
cpi.console.println("Target: " + target)
cpi.console.println("Press A to start")
while not cpi.controller.is_press('a'):
    led(red_led)
while cpi.controller.is_press('a'):
    time.sleep(0.05)
led(off_led)

# PHASE 1: OUTBOUND -------------------------------------
cpi.console.clear()
cpi.console.println("Going to " + target)

reached = False
while not reached:
    if cpi.controller.is_press('a'):
        cpi.mbot2.EM_stop(port="all")
        led(off_led)
        cpi.console.clear()
        cpi.console.println("Aborted")
        raise SystemExit

    l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)

    # Target detected on either probe
    if l1_color == target or r1_color == target:
        # Drive forward a little past the patch
        end = time.time() + OVERSHOOT
        while time.time() < end:
            cpi.mbot2.drive_power(SPEED, -SPEED)
            time.sleep(0.02)
        cpi.mbot2.EM_stop(port="all")
        reached = True
    else:
        follow_step()
        time.sleep(0.02)

# PHASE 2: DEPOSIT --------------------------------------
cpi.console.clear()
cpi.console.println("Depositing " + target)
led(color_to_led(target))
time.sleep(DEPOSIT_TIME)
led(off_led)

# PHASE 3: U-TURN ---------------------------------------
cpi.console.clear()
cpi.console.println("Turning around")
cpi.mbot2.turn(180, speed=TURN_SPEED)

# PHASE 4: RETURN ---------------------------------------
cpi.console.clear()
cpi.console.println("Returning home")

while True:
    if cpi.controller.is_press('a'):
        break

    l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)

    # Yellow detected = back at start
    if l1_color == "yellow" or r1_color == "yellow":
        cpi.mbot2.EM_stop(port="all")
        cpi.console.clear()
        cpi.console.println("Home!")
        led(yellow_led)
        time.sleep(2)
        led(off_led)
        break

    follow_step()
    time.sleep(0.02)

# DONE --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.led.off()
