import cv2
import time
import numpy as np
import autopy
import pyautogui
import HandTrackingModule as htm

# Camera setup
wCam, hCam = 640, 480
smoothening = 7

pLocX, pLocY = 0, 0  # Previous cursor location
cLocX, cLocY = 0, 0  # Current cursor location

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=1)
wScr, hScr = autopy.screen.size()

pTime = 0

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]  # Index finger
        x2, y2 = lmList[12][1:]  # Middle finger
        fingers = detector.fingersUp()

        # Move cursor: only index finger up
        if fingers[1] == 1 and fingers[2] == 0:
            x3 = np.interp(x1, (0, wCam), (0, wScr))
            y3 = np.interp(y1, (0, hCam), (0, hScr))

            # Smooth cursor
            cLocX = pLocX + (x3 - pLocX) / smoothening
            cLocY = pLocY + (y3 - pLocY) / smoothening

            # Clamp to screen edges
            cLocX = max(0, min(wScr, cLocX))
            cLocY = max(0, min(hScr, cLocY))

            autopy.mouse.move(wScr - cLocX, cLocY)
            pLocX, pLocY = cLocX, cLocY

            # Draw cursor circle
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)

        # Left click: Index + Middle fingers close
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
            length, img, _ = detector.findDistance(8, 12, img)
            if length < 40:
                cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.click()

        # Right click: Index + Middle + Ring fingers close
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
            length, img, _ = detector.findDistance(8, 16, img)
            if length < 50:
                cv2.circle(img, (x1, y1), 15, (0, 0, 255), cv2.FILLED)
                autopy.mouse.click(button=autopy.mouse.Button.RIGHT)

        # Drag & Drop: Thumb + Index pinch
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0:
            length, img, _ = detector.findDistance(4, 8, img)
            if length < 40:
                autopy.mouse.toggle(autopy.mouse.Button.LEFT, True)  # Hold
            else:
                autopy.mouse.toggle(autopy.mouse.Button.LEFT, False)  # Release

        # Two-finger scroll using pyautogui
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
            length, img, _ = detector.findDistance(8, 12, img, draw=False)
            if length > 100:
                pyautogui.scroll(-20)  # Scroll down
            else:
                pyautogui.scroll(20)   # Scroll up

    # If hand is removed, cursor stays at last position
    # No action needed, pLocX/pLocY remain unchanged

    # FPS counter
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_PLAIN, 2,
                (255, 0, 0), 2)

    cv2.imshow("Virtual Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
