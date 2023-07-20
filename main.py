from pywinauto import application, mouse, findwindows
from pynput import keyboard
import os
import sys
import numpy as np
import cv2
import time

STOP_SCRIPT_KEY = keyboard.Key.f1
PAUSE_SCRIPT_KEY = keyboard.Key.f2
PATH_TO_TEMPLATES = "templates/"
FIND_MATCH_THRESHOLD = 0.85
FIND_ALL_MATCH_THRESHOLD = 0.85
NEARBY_THRESHOLD_DISTANCE = 50

def is_nearby_coords(coord1, coord2, threshold_distance=NEARBY_THRESHOLD_DISTANCE):
    x1, y1 = coord1
    x2, y2 = coord2
    distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance <= threshold_distance

def find_match(template, threshold=FIND_MATCH_THRESHOLD):
    image = cv2.cvtColor(np.array(dialog.capture_as_image()), cv2.COLOR_RGB2GRAY)
    template_width, template_height = template.shape[::-1]

    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    for pt in zip(*loc[::-1]):
        return (pt[0] + template_width // 2, pt[1] + template_height // 2) # type: ignore

def find_all_matches(template, threshold=FIND_ALL_MATCH_THRESHOLD):
    screen_capture = cv2.cvtColor(
        np.array(dialog.capture_as_image()), cv2.COLOR_RGB2GRAY)
    template_width, template_height = template.shape[::-1]

    result = cv2.matchTemplate(screen_capture, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    matches = []
    for pt in zip(*loc[::-1]):
        match_coords = (pt[0] + template_width // 2, pt[1] + template_height // 2) # type: ignore

        is_nearby = False

        if not matches:
            matches.append(match_coords)
        else:
            for match in matches:
                if is_nearby_coords(match, match_coords) or match == match_coords:
                    is_nearby = True
                    break

        if not is_nearby:
            matches.append(match_coords)

    return matches

def on_press(key):
    global end, paused
    if key == STOP_SCRIPT_KEY:
        end = True
    if key == PAUSE_SCRIPT_KEY:
        if paused:
            print("Unpaused")
            paused = False
        else:
            print("Paused")
            paused = True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("No instance window title provided.")
    else:
        handle = findwindows.find_window(title=sys.argv[1])
        app = application.Application().connect(handle=handle)
        dialog = app.top_window()
        dialog.maximize()
        dialog.set_focus()

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        end = False
        paused = False

        templates = {}
        for file in os.listdir(PATH_TO_TEMPLATES):
            if file.endswith(".png"):
                templates[file] = cv2.imread(os.path.join(PATH_TO_TEMPLATES, file), cv2.IMREAD_GRAYSCALE)
        if not templates:
            raise Exception("No templates found!")

        upgrade_available = False
        upgrade_indicators = []

        while not end:
            if not paused:
                if upgrade_available:
                    print("Entering upgrade menu...")

                    start_time = time.time() # Start counting time in upgrade menu

                    if not upgrade_indicators:
                        print("No upgrade indicators found, attempting to locate.")
                        upgrade_indicators = find_all_matches(templates["upgrade_indicator.png"])

                    print("Upgrade indicators available. Coordinates are")
                    print(upgrade_indicators)

                    count = len(upgrade_indicators) - 1

                    while upgrade_available and not paused and count >= 0:
                        if (time.time() - start_time) > 30: # Exit upgrade menu if 30 seconds elapsed in upgrade menu
                            upgrade_available = False
                        else:
                            print(f"Clicking upgrade indicator at {upgrade_indicators[count]}")
                            mouse.click(button="left", coords=upgrade_indicators[count]) # Click upgrade indicator
                            time.sleep(0.5) # Allow animations to play

                            # Click close button if it pops up
                            close_button = find_match(templates["close.png"])
                            if close_button:
                                mouse.click(button="left", coords=close_button)

                            # Click collect button if it pops up
                            collect_button = find_match(templates["collect.png"])
                            if collect_button:
                                mouse.click(button="left", coords=collect_button)

                            count -= 1

                    upgrade_available = False

                for filename, template in templates.items():
                    coords = find_match(template)
                    if coords:
                        if filename == "upgrade_available.png":
                            print("Upgrade available, attempting to enter upgrade menu...")

                            # Click build button 10 times to ensure user enters upgrade menu
                            for _ in range(10):
                                mouse.click(button="left", coords=coords)

                            upgrade_available = True
                            break
                        else:
                            print(f"Found {filename}, sending click.")
                            mouse.click(button="left", coords=coords)

        listener.stop()
