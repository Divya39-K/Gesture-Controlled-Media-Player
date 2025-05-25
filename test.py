import cv2
import mediapipe as mp
import pyautogui
import time

# --- MORE ROBUST Finger Counting Logic ---
def count_fingers(lst):
    cnt = 0
    # Check if landmark list is valid and has enough points
    if not lst or not lst.landmark or len(lst.landmark) < 21:
        # print("Warning: Incomplete landmarks received.") # Optional debug print
        return 0 # Cannot count if landmarks are missing/incomplete

    # Define landmark points for tips and PIP/IP joints
    # Tip IDs: 4 (Thumb), 8 (Index), 12 (Middle), 16 (Ring), 20 (Pinky)
    tip_ids = [4, 8, 12, 16, 20]
    # PIP/IP Joint IDs (one joint below the tip)
    # Use IP for Thumb (3), PIP for others (6, 10, 14, 18)
    pip_dip_ids = [3, 6, 10, 14, 18] # Using IP joint (3) for thumb comparison

    try: # Add error handling for landmark access
        # --- Check the four main fingers (Index, Middle, Ring, Pinky) ---
        # Finger is considered UP if its tip's Y coordinate is *less* than its PIP joint's Y coordinate
        # (Assumes Y decreases going up the screen in typical image coordinates)
        for i in range(1, 5): # Loop through Index, Middle, Ring, Pinky (indices 1 to 4 in tip_ids/pip_dip_ids)
            tip_y = lst.landmark[tip_ids[i]].y
            pip_y = lst.landmark[pip_dip_ids[i]].y
            # print(f"Finger {i+1}: TipY={tip_y:.3f}, PIP_Y={pip_y:.3f}") # Debug print

            if tip_y < pip_y:
                cnt += 1

        # --- Check the Thumb ---
        # Thumb is considered UP if its tip's Y coordinate is significantly *less* than its IP joint's Y coordinate
        thumb_tip_y = lst.landmark[tip_ids[0]].y  # Landmark 4
        thumb_ip_y = lst.landmark[pip_dip_ids[0]].y # Landmark 3
        # print(f"Thumb: TipY={thumb_tip_y:.3f}, IP_Y={thumb_ip_y:.3f}") # Debug print

        # A simple vertical check for the thumb might be sufficient if held relatively upright
        if thumb_tip_y < thumb_ip_y:
            cnt += 1
        # Optional: More robust thumb check using horizontal distance from base if needed
        # Example: Check if thumb tip (4) is horizontally further out than IP joint (3)
        # thumb_tip_x = lst.landmark[tip_ids[0]].x
        # thumb_ip_x = lst.landmark[pip_dip_ids[0]].x
        # wrist_x = lst.landmark[0].x # Use wrist as reference
        # if (wrist_x < 0.5 and thumb_tip_x < thumb_ip_x - 0.01) or \
        #    (wrist_x >= 0.5 and thumb_tip_x > thumb_ip_x + 0.01):
        #      cnt += 1


    except IndexError:
        # print("Warning: Landmark index out of range during count.") # Optional debug print
        return 0 # Return 0 if there's an issue accessing landmarks
    except AttributeError:
        # print("Warning: Landmark attribute error during count.") # Optional debug print
        return 0 # Return 0 if landmarks don't have expected attributes

    return cnt
# --- End Finger Counting Logic ---

# Initialize video capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open video capture device.")
    exit()

# MediaPipe Hand Landmark setup
drawing = mp.solutions.drawing_utils
hands = mp.solutions.hands
# Set confidence levels for detection and tracking
hand_obj = hands.Hands(max_num_hands=1,
                       min_detection_confidence=0.6,
                       min_tracking_confidence=0.6)

# Variables for debouncing (preventing rapid key presses)
start_init = False
prev = -1 # Initialize prev to a value different from possible counts (0-5)
start_time = 0 # Initialize start_time

# --- Main Loop ---
while True:
    end_time = time.time() # Get current time for debouncing check

    # Read frame from camera
    ret, frm = cap.read()
    if not ret:
        print("Error: Failed to read frame from camera.")
        break # Exit loop if frame reading fails

    # Flip frame horizontally for a natural mirror view
    frm = cv2.flip(frm, 1)

    # Get frame dimensions
    h, w, _ = frm.shape

    # Process the frame with MediaPipe Hands
    # Convert the BGR image to RGB.
    rgb_frame = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB)

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    rgb_frame.flags.writeable = False
    res = hand_obj.process(rgb_frame)
    rgb_frame.flags.writeable = True # Make writable again if needed later

    # Prepare finger count display text
    finger_count_display = "Fingers: ?" # Default text when no hand is detected

    # If hand landmarks are detected
    if res.multi_hand_landmarks:
        # Extract landmarks for the first detected hand
        hand_keyPoints = res.multi_hand_landmarks[0]

        # Count the number of extended fingers using the new logic
        cnt = count_fingers(hand_keyPoints)
        finger_count_display = f"Fingers: {cnt}" # Update display text with current count

        # --- Debouncing and Action Logic ---
        # Check if the finger count has changed since the last stable action
        if not (prev == cnt):
            if not start_init: # If this is the first frame the count changed, start the timer
                start_time = time.time()
                start_init = True
            # If count changed before and enough time has passed (gesture is stable)
            elif (end_time - start_time) > 0.2: # Debounce time (adjust if needed)

                # Perform actions based on the *new* stable finger count
                if (cnt == 1):
                    pyautogui.press("space") # Play/Pause
                    print(f"Action Triggered: Space/Pause (Fingers: {cnt})")
                elif (cnt == 2):
                    pyautogui.press("space") # Play/Pause
                    print(f"Action Triggered: Space/Pause (Fingers: {cnt})")
                elif (cnt == 3):
                    pyautogui.press("up")    # Volume Up
                    print(f"Action Triggered: Up (Fingers: {cnt})")
                elif (cnt == 4):
                    pyautogui.press("down")  # Volume Down
                    print(f"Action Triggered: Down (Fingers: {cnt})")
                elif (cnt == 5):
                    pyautogui.press("esc")   # Escape Key
                    print(f"Action Triggered: ESC (Fingers: {cnt})")

                # Update previous count to the current count and reset the timer flag
                prev = cnt
                start_init = False
        # --- End Debouncing Logic ---

        # Draw the hand annotations on the original BGR frame ('frm')
        drawing.draw_landmarks(frm, hand_keyPoints, hands.HAND_CONNECTIONS)
    else:
        # If no hands are detected in the current frame
        prev = -1 # Reset previous state
        start_init = False # Reset timer state
        finger_count_display = "Fingers: 0" # Display 0 when no hand is visible

    # --- Display Information on Frame ---
    # Display the finger count
    cv2.putText(frm, finger_count_display, (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    # Display updated instructions
    instructions = [
        "1 or 2: Pause/Play (Space)",
        "3: Up",
        "4: Down",
        "5: ESC",
        "Esc: Quit Script"
    ]
    y0, dy = 30, 30 # Starting Y position and line spacing for instructions
    for i, line in enumerate(instructions):
         y = y0 + i * dy
         cv2.putText(frm, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2, cv2.LINE_AA)
    # --- End Display Information ---

    # Show the processed frame in a window
    cv2.imshow("Hand Gesture Media Control", frm)

    # Check for the physical ESC key press on the keyboard to exit the script
    if cv2.waitKey(1) == 27:
        print("Keyboard ESC key pressed. Exiting script...")
        break # Exit the main while loop

# Release resources when the loop ends
cap.release()
cv2.destroyAllWindows()
print("Resources released.")