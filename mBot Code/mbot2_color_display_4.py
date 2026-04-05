import cyberpi as cpi
import time

# -------------------------------------------------------
# mBot2 – Drive straight & display last detected colour
#
# - Press A to start. Robot drives forward.
# - The QuadRGB sensor checks for colour every 0.1s.
# - The screen updates whenever the colour changes.
# - Press A again to stop. Last colour stays on screen.
# -------------------------------------------------------

DRIVE_SPEED = 50  # forward speed (0-100)

# FUNCTIONS ---------------------------------------------
def show_color(color_name):
    cpi.console.clear()
    cpi.console.println("Color:")
    cpi.console.println(color_name.upper())

def get_color():
    # Returns the colour name seen by probe L1 (index 1)
    # get_gray returns 0-100; we use get_color_sta for colour name
    return cpi.quad_rgb_sensor.get_color_sta('l1', index=1)

# WAIT TO START -----------------------------------------
cpi.console.println('Press A to start')
while not cpi.controller.is_press('a'):
    cpi.led.on(255, 0, 0)
# Wait for button to be released before continuing
while cpi.controller.is_press('a'):
    time.sleep(0.05)

cpi.led.on(0, 255, 0)

# MAIN LOOP ---------------------------------------------
last_color = ""
cpi.mbot2.forward(speed=DRIVE_SPEED)  # drive straight forever

while True:
    # Press A again to stop
    if cpi.controller.is_press('a'):
        break

    current_color = get_color()

    if current_color != last_color and current_color != "":
        last_color = current_color
        show_color(current_color)

    time.sleep(0.1)

# STOP --------------------------------------------------
cpi.mbot2.EM_stop(port="all")
cpi.led.off()
cpi.console.clear()
cpi.console.println("Stopped!")
cpi.console.println("Last color:")
cpi.console.println(last_color.upper() if last_color else "NONE")
