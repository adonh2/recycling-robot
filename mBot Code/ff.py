import cyberpi as cpi
import time

# --- Webcam bridge config ---
WIFI_SSID = "geezer"
WIFI_PASS = "gegezer123"
DETECT_URL = ""   # <-- IP of the PC running detect.py

cpi.wifi.connect(WIFI_SSID, WIFI_PASS)
cpi.console.println("Connecting WiFi...")
for _ in range(40):
    if cpi.wifi.is_connect():
        break
    time.sleep(0.25)
cpi.console.clear()

# -------------------------------------------------------
# mBot2 - Recycling Robot
#
# A = start the run
# B = restart (back to Press A screen at any time)
#
# 1. Follow black line until input colour detected
# 2. Turn:  red or green → 90° anticlockwise
#           blue or purple → 90° clockwise
# 3. Drive forward until any sensor detects black
# 4. Follow branch until input colour detected (DROP)
# 5a. Reverse: wait for all sensors to see white,
#     then wait until any sensor detects black,
#     then drive forward for 1 second
# 5b. Turn 90° opposite of phase 2
# 5c. Reverse straight until yellow detected (HOME)
# -------------------------------------------------------

input = "red"

SPEED       = 22
TURN_SPEED  = 30
DETECT_DIST = 10

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

def fetch_detected_color():
    """Poll detect.py server. Returns 'red'/'blue'/'green'/'purple' or None."""
    try:
        # API name may vary slightly between cyberpi versions:
        # try cpi.cloud.web_request_get / cpi.cloud.web_request("GET", ...) if this fails
        resp = cpi.cloud.web_request_get(DETECT_URL)
        if resp:
            resp = resp.strip().lower()
            if resp in ("red", "blue", "green", "purple"):
                return resp
    except:
        pass
    return None

def follow_step(any_color=False):
    """One step of line following. L2/R2 = outer alignment guards,
    L1/R1 = fine steering. Returns L1 and R1 colour names.
    any_color=True treats all non-white, non-yellow as line."""
    l2_color = cpi.quad_rgb_sensor.get_color_sta('l2', index=1)
    l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)
    r2_color = cpi.quad_rgb_sensor.get_color_sta('r2', index=1)

    if any_color:
        L2 = l2_color not in ("white", "yellow")
        L1 = l1_color not in ("white", "yellow")
        R1 = r1_color not in ("white", "yellow")
        R2 = r2_color not in ("white", "yellow")
    else:
        L2 = l2_color == "black"
        L1 = l1_color == "black"
        R1 = r1_color == "black"
        R2 = r2_color == "black"

    # Outer guards: big drift, moderate correction (not a full pivot)
    if L2 and not R2:
        # Far-left sees line - robot drifted right, steer left
        cpi.mbot2.drive_power(SPEED // 4, -SPEED)
    elif R2 and not L2:
        # Far-right sees line - robot drifted left, steer right
        cpi.mbot2.drive_power(SPEED, -SPEED // 4)
    # Inner sensors: gentle steering
    elif L1 and R1:
        cpi.mbot2.drive_power(SPEED, -SPEED)
    elif L1:
        cpi.mbot2.drive_power(SPEED // 2, -SPEED)
    elif R1:
        cpi.mbot2.drive_power(SPEED, -SPEED // 2)
    else:
        cpi.mbot2.drive_power(SPEED // 2, -SPEED // 2)

    return l1_color, r1_color

def follow_step_reverse():
    """Same as follow_step but drives in reverse. Returns L1 and R1 colours."""
    l2_color = cpi.quad_rgb_sensor.get_color_sta('l2', index=1)
    l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
    r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)
    r2_color = cpi.quad_rgb_sensor.get_color_sta('r2', index=1)

    L2 = l2_color == "black"
    L1 = l1_color == "black"
    R1 = r1_color == "black"
    R2 = r2_color == "black"

    # Inverted versions of forward corrections
    if L2 and not R2:
        cpi.mbot2.drive_power(-SPEED // 4, SPEED)
    elif R2 and not L2:
        cpi.mbot2.drive_power(-SPEED, SPEED // 4)
    elif L1 and R1:
        cpi.mbot2.drive_power(-SPEED, SPEED)
    elif L1:
        cpi.mbot2.drive_power(-SPEED // 2, SPEED)
    elif R1:
        cpi.mbot2.drive_power(-SPEED, SPEED // 2)
    else:
        cpi.mbot2.drive_power(-SPEED // 2, SPEED // 2)

    return l1_color, r1_color

# OUTER LOOP - B always brings us back here -------------
while True:

    # WAIT TO START -------------------------------------
    cpi.console.clear()
    cpi.console.println("Target: " + input)
    cpi.console.println("A / item / webcam")
    poll_counter = 0
    while True:
        led(color_to_rgb(input))
        dist = cpi.ultrasonic2.get(index=1)

        # Manual start (button or item placed in front)
        if cpi.controller.is_press('a') or (dist > 0 and dist < DETECT_DIST):
            break

        # Auto start from webcam (poll every ~0.5 s to stay responsive)
        poll_counter += 1
        if poll_counter >= 5:
            poll_counter = 0
            detected = fetch_detected_color()
            if detected:
                input = detected
                cpi.console.clear()
                cpi.console.println("Webcam: " + input)
                cpi.console.println("Auto-starting...")
                time.sleep(1)
                break

        # Manual D-pad override (unchanged)
        if cpi.controller.is_press('up'):
            input = "red"
            cpi.console.clear(); cpi.console.println("Target: " + input)
            cpi.console.println("A / item / webcam"); time.sleep(0.2)
        elif cpi.controller.is_press('right'):
            input = "blue"
            cpi.console.clear(); cpi.console.println("Target: " + input)
            cpi.console.println("A / item / webcam"); time.sleep(0.2)
        elif cpi.controller.is_press('down'):
            input = "green"
            cpi.console.clear(); cpi.console.println("Target: " + input)
            cpi.console.println("A / item / webcam"); time.sleep(0.2)
        elif cpi.controller.is_press('left'):
            input = "purple"
            cpi.console.clear(); cpi.console.println("Target: " + input)
            cpi.console.println("A / item / webcam"); time.sleep(0.2)

        time.sleep(0.1)
    while cpi.controller.is_press('a'):
        time.sleep(0.05)
    led(off)

    restart = False

    restart = False

    # STARTUP: Drive forward until clear of starting yellow zone
    cpi.console.clear()
    cpi.console.println("Leaving start...")
    while True:
        if b_pressed():
            restart = True
            break
        cpi.mbot2.drive_power(SPEED, -SPEED)
        yellow_seen = any(
            cpi.quad_rgb_sensor.get_color_sta(p, index=1) == "yellow"
            for p in ('l2', 'l1', 'r1', 'r2')
        )
        if not yellow_seen:
            cpi.mbot2.EM_stop(port="all")
            break
        time.sleep(0.02)
    if restart: continue

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
            cpi.console.println("Dropped off")
            time.sleep(1)
            break
        time.sleep(0.02)
    if restart: continue

    # PHASE 5: Reverse tracking the lane ----------------
    cpi.console.clear()
    cpi.console.println("Reversing...")
    led(off)

    # 5.1: reverse following the black line until all sensors white
    while True:
        if b_pressed():
            restart = True
            break
        follow_step_reverse()
        all_white = all(
            cpi.quad_rgb_sensor.get_color_sta(p, index=1) == "white"
            for p in ('l2', 'l1', 'r1', 'r2')
        )
        if all_white:
            cpi.mbot2.EM_stop(port="all")
            break
        time.sleep(0.02)
    if restart: continue

    # 5.2: Turn 90° opposite of phase 2
    cpi.console.clear()
    cpi.console.println("Turning")
    if input in ("red", "green"):
        cpi.mbot2.turn(90, speed=TURN_SPEED)
    elif input in ("blue", "purple"):
        cpi.mbot2.turn(-90, speed=TURN_SPEED)
    if b_pressed():
        continue

    # 5.3: Drive forward following line until yellow detected
    cpi.console.clear()
    cpi.console.println("Going to yellow")
    uturn_count = 0
    while True:
        if b_pressed():
            restart = True
            break
        dist = cpi.ultrasonic2.get(index=1)
        if 0 < dist < DETECT_DIST:
            cpi.mbot2.EM_stop(port="all")
            while True:
                if b_pressed():
                    restart = True
                    break
                dist = cpi.ultrasonic2.get(index=1)
                if dist == 0 or dist >= DETECT_DIST:
                    break
                cpi.audio.play("beeps")
                time.sleep(0.3)
            if restart: break
        l1_color, r1_color = follow_step(any_color=True)
        if l1_color == "yellow" or r1_color == "yellow":
            cpi.mbot2.EM_stop(port="all")
            break
        all_white = all(
            cpi.quad_rgb_sensor.get_color_sta(p, index=1) == "white"
            for p in ('l2', 'l1', 'r1', 'r2')
        )
        if all_white:
            cpi.mbot2.EM_stop(port="all")
            uturn_count += 1
            if uturn_count > 2:
                cpi.console.clear()
                cpi.console.println("Lost! Press B")
                while not b_pressed():
                    cpi.audio.play("beeps")
                    time.sleep(0.3)
                restart = True
                break
            cpi.mbot2.turn(180, speed=TURN_SPEED)
        time.sleep(0.02)
    if restart: continue
    led(yellow)
    cpi.mbot2.turn(180, speed=TURN_SPEED)

    # Reverse until yellow detected
    while True:
        if b_pressed():
            restart = True
            break
        cpi.mbot2.drive_power(-SPEED, SPEED)
        l1_color = cpi.quad_rgb_sensor.get_color_sta('l1', index=1)
        r1_color = cpi.quad_rgb_sensor.get_color_sta('r1', index=1)
        if l1_color == "yellow" or r1_color == "yellow":
            cpi.mbot2.EM_stop(port="all")
            break
        time.sleep(0.02)
    if restart: continue
    time.sleep(0.5)

    # Reverse until black detected
    while True:
        if b_pressed():
            restart = True
            break
        cpi.mbot2.drive_power(-SPEED, SPEED)
        if any_sensor_black():
            cpi.mbot2.EM_stop(port="all")
            break
        time.sleep(0.02)
    if restart: continue

    led(off)