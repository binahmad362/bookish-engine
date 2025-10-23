import pyautogui
import time
import subprocess
import requests
import os
import keyboard
import cv2
import numpy as np

# Enable failsafe - move mouse to top-left corner to abort
pyautogui.FAILSAFE = False

# List of scales to try for template matching
scales = [0.5, 0.75, 1.0, 1.25, 1.5]

# Define rectangular areas for different UI elements (x, y, width, height)
rectangles = [
    (0, 0, 1920, 1080),  # Full screen (adjust based on your screen resolution)
    # Add more specific regions as needed
]

def find_template(template_path, timeout=10, confidence=0.8):
    """Find template using multi-scale approach like the first script"""
    print(f"Searching for {template_path} on screen...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Take a screenshot
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # Load the template image
        template = cv2.imread(template_path, 0)
        if template is None:
            print(f"Error: Could not load template {template_path}")
            return None
        
        tw, th = template.shape[::-1]
        best_val = 0
        best_loc = None
        best_size = None
        best_rect = None

        # Loop through each rectangular area
        for rect in rectangles:
            x, y, w, h = rect
            region = gray_screenshot[y:y+h, x:x+w]

            # Perform template matching at different scales
            for scale in scales:
                resized_template = cv2.resize(template, (int(tw * scale), int(th * scale)))
                res = cv2.matchTemplate(region, resized_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val > best_val:
                    best_val = max_val
                    best_loc = max_loc
                    best_size = resized_template.shape[::-1]
                    best_rect = (x, y)

        if best_val >= confidence:
            if best_loc and best_size and best_rect:
                offset_x, offset_y = best_rect
                center_x = offset_x + best_loc[0] + best_size[0] // 2
                center_y = offset_y + best_loc[1] + best_size[1] // 2
                print(f"Found {template_path} with confidence {best_val:.2f} at ({center_x}, {center_y})")
                return (center_x, center_y)
        
        time.sleep(0.1)  # Small sleep to prevent CPU overload
    
    print(f"❌ {template_path} not found on screen within {timeout} seconds")
    return None

def wait_and_click(image, timeout=10, confidence=0.8):
    """Wait for an image to appear and click it using multi-scale template matching"""
    location = find_template(image, timeout, confidence)
    if location:
        center_x, center_y = location
        print(f"Clicking at center: X: {center_x}, Y: {center_y}")
        pyautogui.click(center_x, center_y)
        print(f"Successfully clicked {image}!")
        return True
    return False

def wait_for_image(image, timeout=10, confidence=0.8):
    """Wait for an image to appear without clicking it using multi-scale template matching"""
    location = find_template(image, timeout, confidence)
    return location is not None

# Download and read the numbers file
def download_numbers_file():
    url = "https://raw.githubusercontent.com/binahmad362/bookish-octo-couscous/main/rough.txt"
    try:
        print("Downloading numbers file...")
        response = requests.get(url)
        response.raise_for_status()
        
        with open("rough.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Numbers file downloaded successfully!")
        return True
    except Exception as e:
        print(f"Error downloading numbers file: {e}")
        return False

def read_numbers_file():
    try:
        with open("rough.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if len(lines) < 3:
            print("Error: File doesn't contain enough data")
            return None, None, []
        
        country_name = lines[0]
        country_code = lines[1]
        numbers = lines[2:]
        
        print(f"Country: {country_name}")
        print(f"Country code: {country_code}")
        print(f"Numbers to check: {len(numbers)}")
        
        return country_name, country_code, numbers
    except Exception as e:
        print(f"Error reading numbers file: {e}")
        return None, None, []

def save_not_usable_number(number):
    try:
        with open("not_usable.txt", "a", encoding="utf-8") as f:
            f.write(number + "\n")
        print(f"Saved {number} to not_usable.txt")
    except Exception as e:
        print(f"Error saving to not_usable.txt: {e}")

def save_request_review_number(number):
    try:
        with open("request_review.txt", "a", encoding="utf-8") as f:
            f.write(number + "\n")
        print(f"Saved {number} to request_review.txt")
    except Exception as e:
        print(f"Error saving to request_review.txt: {e}")

def type_with_delay(text, delay=0.1):
    """Type text with specified delay between characters"""
    pyautogui.write(text, interval=delay)

def check_too_long_phone_number():
    """Check if too_long_phone_number.png is on screen and handle it - QUICK VERSION"""
    if wait_for_image('too_long_phone_number.png', timeout=2):
        print("⚠️ Too long phone number detected! Handling the error...")
        
        # Click ok.png
        if wait_and_click('ok.png', timeout=5):
            print("Clicked ok.png to dismiss the error")
            time.sleep(1)
            
            # Press backspace 50 times to clear everything
            print("Clearing phone number field with 50 backspaces...")
            for _ in range(50):
                keyboard.press_and_release('backspace')
            time.sleep(1)
            
            print("Phone number field cleared successfully")
            return True
        else:
            print("Failed to find ok.png")
            return False
    return False

def process_numbers(country_name, country_code, numbers):
    """Process all numbers through the WhatsApp verification flow - OPTIMIZED"""
    
    # Check for too_long_phone_number.png before starting
    if check_too_long_phone_number():
        print("Recovered from too_long_phone_number error, continuing...")
    
    # Click select_country.png
    if not wait_and_click('select_country.png', timeout=10):
        print("Failed to find select_country.png. Aborting.")
        return
    
    time.sleep(2)
    
    # Check for too_long_phone_number.png after clicking select_country
    if check_too_long_phone_number():
        print("Recovered from too_long_phone_number error, continuing...")
    
    # Click search_the_country.png
    if not wait_and_click('search_the_country.png', timeout=10):
        print("Failed to find search_the_country.png. Aborting.")
        return
    
    time.sleep(1)
    
    # Check for too_long_phone_number.png after clicking search_the_country
    if check_too_long_phone_number():
        print("Recovered from too_long_phone_number error, continuing...")
    
    # Type country name
    print(f"Typing country: {country_name}")
    type_with_delay(country_name)
    time.sleep(1)
    
    # Check for too_long_phone_number.png after typing country name
    if check_too_long_phone_number():
        print("Recovered from too_long_phone_number error, continuing...")
    
    # Click confirm_the_country.png
    if not wait_and_click('confirm_the_country.png', timeout=10):
        print("Failed to find confirm_the_country.png. Aborting.")
        return
    
    time.sleep(2)
    
    # Check for too_long_phone_number.png after clicking confirm_the_country
    if check_too_long_phone_number():
        print("Recovered from too_long_phone_number error, continuing...")
    
    # Process each number
    for i, full_number in enumerate(numbers):
        print(f"\n--- Processing number {i+1}/{len(numbers)}: {full_number} ---")
        
        # Check for too_long_phone_number.png before processing each number
        if check_too_long_phone_number():
            print("Recovered from too_long_phone_number error, continuing with current number...")
        
        # Remove country code from the number
        if full_number.startswith(country_code):
            number_without_code = full_number[len(country_code):]
        else:
            number_without_code = full_number
            print(f"Warning: Number doesn't start with country code {country_code}")
        
        print(f"Typing number without country code: {number_without_code}")
        
        # Type the number without country code
        type_with_delay(number_without_code)
        time.sleep(0.5)
        
        # Check for too_long_phone_number.png after typing number
        if check_too_long_phone_number():
            print("Recovered from too_long_phone_number error, re-typing current number...")
            # Re-type the number since it was cleared
            type_with_delay(number_without_code)
            time.sleep(0.5)
        
        # Click next.png
        if not wait_and_click('next.png', timeout=10):
            print("Failed to find next.png. Moving to next number.")
            continue
        
        # Check for too_long_phone_number.png after clicking next
        if check_too_long_phone_number():
            print("Recovered from too_long_phone_number error, continuing to next number...")
            continue
        
        # Wait for result (edit.png or not_usable.png) - QUICK VERSION
        print("Waiting for result (edit.png or not_usable.png)...")
        result_found = False
        start_time = time.time()
        
        while time.time() - start_time < 8 and not result_found:
            # Check for edit.png
            if wait_for_image('edit.png', timeout=0.5):
                print("Edit button found - number might be valid but needs modification")
                # Click edit.png to clear field
                wait_and_click('edit.png', timeout=2)
                # Clear the field with backspaces
                for _ in range(20):
                    keyboard.press_and_release('backspace')
                time.sleep(1)
                result_found = True
                break
            
            # Check for not_usable.png
            if wait_for_image('not_usable.png', timeout=0.5):
                print("Number is not usable - saving to file")
                save_not_usable_number(full_number)
                # Click not_usable.png
                wait_and_click('not_usable.png', timeout=2)
                result_found = True
                break
            
            time.sleep(0.1)
        
        if not result_found:
            print("Neither edit.png nor not_usable.png found - unexpected state")
            # Try to go back or reset state
            pyautogui.press('esc')
            time.sleep(2)
            
            # Check for too_long_phone_number.png after pressing escape
            if check_too_long_phone_number():
                print("Recovered from too_long_phone_number error, continuing to next number...")
                continue
            
            # Check if we're back at number entry screen
            if wait_and_click('register_new_number.png', timeout=5):
                print("Back at registration screen, continuing...")
            else:
                print("Could not recover to registration screen")
                continue
            continue
        
        # Handle registration flow after not_usable
        if wait_for_image('not_usable.png', timeout=1):
            # Check for register_new_number.png first
            if wait_and_click('register_new_number.png', timeout=8):
                # Check for too_long_phone_number.png after clicking register_new_number
                if check_too_long_phone_number():
                    print("Recovered from too_long_phone_number error, continuing to next number...")
                    continue
                
                # Click agree.png if needed
                wait_and_click('agree_2.png', timeout=5)
                
                # Check for too_long_phone_number.png after clicking agree_2
                if check_too_long_phone_number():
                    print("Recovered from too_long_phone_number error, continuing to next number...")
                    continue
                
                # Wait before processing next number
                time.sleep(2)
            else:
                # If register_new_number.png is not found, check for request_review.png
                print("Failed to find register_new_number.png, checking for request_review.png...")
                
                # Check for too_long_phone_number.png before checking request_review
                if check_too_long_phone_number():
                    print("Recovered from too_long_phone_number error, continuing to next number...")
                    continue
                
                if wait_for_image('request_review.png', timeout=5):
                    print("Found request_review.png - saving number to request_review.txt")
                    save_request_review_number(full_number)
                    
                    # Click show_option.png
                    if wait_and_click('show_option.png', timeout=8):
                        # Check for too_long_phone_number.png after clicking show_option
                        if check_too_long_phone_number():
                            print("Recovered from too_long_phone_number error, continuing to next number...")
                            continue
                        
                        time.sleep(1)
                        
                        # Click register_new_number_after_it_is_review.png
                        if wait_and_click('register_new_number_after_it_is_review.png', timeout=8):
                            # Check for too_long_phone_number.png after clicking register_new_number_after_it_is_review
                            if check_too_long_phone_number():
                                print("Recovered from too_long_phone_number error, continuing to next number...")
                                continue
                            
                            time.sleep(1)
                            
                            # Click agree_2.png
                            if wait_and_click('agree_2.png', timeout=8):
                                # Check for too_long_phone_number.png after clicking agree_2
                                if check_too_long_phone_number():
                                    print("Recovered from too_long_phone_number error, continuing to next number...")
                                    continue
                                
                                print("Successfully navigated through request review flow")
                                time.sleep(2)
                            else:
                                print("Failed to find agree_2.png after request review")
                        else:
                            print("Failed to find register_new_number_after_it_is_review.png")
                    else:
                        print("Failed to find show_option.png")
                else:
                    print("Neither register_new_number.png nor request_review.png found")

def main():
    # Open MuMu_Installer.exe without blocking
    print("Opening MuMu_Installer.exe...")
    subprocess.Popen("MuMu_Installer.exe")

    # Wait 3 seconds for the installer to load
    print("Waiting 3 seconds for installer to load...")
    time.sleep(3)

    # Look for the install.png image on screen using multi-scale approach
    if not wait_and_click('install.png', timeout=30):
        print("Failed to find install.png. Aborting.")
        return

    # Wait for installation to complete
    print("Waiting for installation to complete...")
    time.sleep(70)

    # Click option.png using multi-scale approach
    if not wait_and_click('option.png', timeout=30):
        print("Failed to find option.png. Aborting.")
        return

    # Wait a moment for options to load
    time.sleep(5)

    # Click backup_restore.png using multi-scale approach
    if not wait_and_click('backup_restore.png', timeout=30):
        print("Failed to find backup_restore.png. Aborting.")
        return

    # Wait a moment for backup/restore options to load
    time.sleep(5)

    # Click restore.png using multi-scale approach
    if not wait_and_click('restore.png', timeout=30):
        print("Failed to find restore.png. Aborting.")
        return

    # Wait for restore dialog to load
    time.sleep(5)

    # Click change_directory.png using multi-scale approach
    if not wait_and_click('change_directory.png', timeout=30):
        print("Failed to find change_directory.png. Aborting.")
        return

    # Wait for directory dialog to load
    time.sleep(1)

    # Type the directory path and press Enter
    print("Typing directory path...")
    pyautogui.write(r'C:\Users\Rdpuser\Desktop\whatsapp')
    pyautogui.press('enter')
    print("Directory path entered successfully!")

    # Wait for directory to load
    time.sleep(5)

    # Double click on mumudata.png using multi-scale approach
    mumudata_location = find_template('mumudata.png', timeout=30)
    if mumudata_location:
        center_x, center_y = mumudata_location
        print(f"Double clicking at center: X: {center_x}, Y: {center_y}")
        pyautogui.doubleClick(center_x, center_y)
        print("Successfully double clicked mumudata.png!")
    else:
        print("Failed to find mumudata.png")
        return

    time.sleep(5)
    
    # Click start_emulator.png using multi-scale approach
    if not wait_and_click('start_emulator.png', timeout=30):
        print("Failed to find start_emulator.png. Aborting.")
        return

    # Wait 60 seconds for emulator to start
    print("Waiting 60 seconds for emulator to start...")
    time.sleep(60)

    # Click WhatsApp icon using multi-scale approach
    if not wait_and_click('whatsapp_icon.png', timeout=30):
        print("Failed to find whatsapp_icon.png. Aborting.")
        return

    time.sleep(5)

    # Click first_agree.png using multi-scale approach
    if not wait_and_click('first_agree.png', timeout=30):
        print("Failed to find first_agree.png. Aborting.")
        return

    time.sleep(5)

    print("Setting up number verification...")
    if not download_numbers_file():
        return
    
    country_name, country_code, numbers = read_numbers_file()
    
    if not country_name or not country_code or not numbers:
        print("Failed to get valid data from numbers file")
        return
    
    print(f"\nStarting automation for {len(numbers)} numbers...")
    print("Make sure WhatsApp is ready for number input!")
    
    # Wait a moment for user to prepare
    time.sleep(2)
    
    # Start processing numbers
    process_numbers(country_name, country_code, numbers)
    
    print("\nAutomation completed! Check not_usable.txt for unusable numbers.")

if __name__ == "__main__":
    main()