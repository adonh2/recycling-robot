import cyberpi as cpi
import time

SPEED      = 30
TURN_SPEED = 30

input = "red"  # only this colour triggers a pause

green  = (0, 255, 0)
green2 = (71,163,145)
red    = (255, 0, 0)
blue   = (0, 0, 255)
off    = (0, 0, 0)
purple = (128, 0, 128)
yellow = (255, 255, 0)

MARKER_COLORS = ("red", "green", "blue", "yellow", "purple", "cyan")

def led(color):
    """Helper to pass a colour tuple to cpi.led.on()"""
    cpi.led.on(color[0], color[1], color[2])

def on_line(probe):
    """Returns True if the probe is on anything other than white."""
    color = cpi.quad_rgb_sensor.get_color_sta(probe, index=1)
    return color != "white"

# WAIT TO START -----------------------------------------
cpi.console.println("Press A to start")
while not cpi.controller.is_press('a'):
    led(red)
while cpi.controller.is_press('a'):
    time.sleep(0.05)

led(off)
cpi.console.clear()
cpi.console.println("Following...")

last_pause_time = 0  # tracks when the last pause happened

# MAIN LOOP ---------------------------------------------
while True:

    if cpi.controller.is_press('a'):
        break

    # Read colours inside the loop so they update each iteration
    l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)

    # Pause only if the detected colour matches input
    # and it hasn't paused within the last 3 seconds
    if (l1_color == input or r1_color == input) and (time.time() - last_pause_time > 3):
        cpi.mbot2.EM_stop(port="all")
        if input == "green":    led(green)
        elif input == "red":    led(red)
        elif input == "blue":   led(blue)
        elif input == "yellow": led(yellow)
        elif input == "purple": led(purple)
        time.sleep(3)
        led(off)
        last_pause_time = time.time()

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
        if l1_color == r1_color:
            if l1_color == "green":
                led(green)
            elif l1_color == "red":
                led(red)
            elif l1_color == "purple":
                led(purple)
            elif l1_color == "blue":
                led(blue)
            elif l1_color == "yellow":
                led(yellow)
            else:
                led(off)
        else:
            led(off)

    elif L1:
        # Drifted right – steer left
        cpi.mbot2.drive_power(SPEED // 4, -SPEED)
        led(off)

    elif R1:
        # Drifted left – steer right
        cpi.mbot2.drive_power(SPEED, -SPEED // 4)
        led(off)

    time.sleep(0.02)

# STOP --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.led.off()
cpi.console.clear()
cpi.console.println("Stopped!")