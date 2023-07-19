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
FIND_ALL_MATCH_THRESHOLD = 0.97

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
         matches.append((pt[0] + template_width // 2, pt[1] + template_height // 2)) # type: ignore

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
        while not end:
            if not paused:
                if upgrade_available:
                    start_time = time.time() # Start counting time in upgrade menu
                    for filename, template in templates.items():
                        if filename == "upgrade_indicator.png":
                            upgrade_indicators = find_all_matches(template)

                            while upgrade_available and not paused:
                                if (time.time() - start_time) > 30: # Exit upgrade menu if 30 seconds elapsed in upgrade menu
                                    upgrade_available = False
                                elif not upgrade_indicators:
                                    upgrade_available = False
                                else:
                                    mouse.click(button="left", coords=upgrade_indicators[0]) # Click upgrade indicator
                                    time.sleep(1.2) # Allow animations to play

                                    # Click close button if it pops up
                                    close_button = find_match(templates["close.png"])
                                    if close_button:
                                        mouse.click(button="left", coords=close_button)

                                    # Click collect button if it pops up
                                    collect_button = find_match(templates["collect.png"])
                                    if collect_button:
                                        mouse.click(button="left", coords=collect_button)

                                    upgrade_indicators.remove(upgrade_indicators[0])

                for filename, template in templates.items():
                    coords = find_match(template)
                    if coords:
                        if filename == "upgrade_available.png":
                            # Click build button 10 times to ensure user enters upgrade menu
                            for _ in range(10):
                                mouse.click(button="left", coords=coords)

                            upgrade_available = True
                            break
                        else:
                            mouse.click(button="left", coords=coords)

        listener.stop()
