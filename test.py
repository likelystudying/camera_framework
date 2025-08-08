import cv2

#0 is iphone se
#1 is iphone 6e
#2 is macbook air
#3 ipad is not recognized

# 0 usually refers to the default camera
cap = cv2.VideoCapture(2)

if not cap.isOpened():
    print("Cannot open camera")
    exit()


# List of known OpenCV VideoCapture property IDs
props = {
    "CAP_PROP_FRAME_WIDTH": cv2.CAP_PROP_FRAME_WIDTH,
    "CAP_PROP_FRAME_HEIGHT": cv2.CAP_PROP_FRAME_HEIGHT,
    "CAP_PROP_FPS": cv2.CAP_PROP_FPS,
    "CAP_PROP_BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
    "CAP_PROP_CONTRAST": cv2.CAP_PROP_CONTRAST,
    "CAP_PROP_SATURATION": cv2.CAP_PROP_SATURATION,
    "CAP_PROP_HUE": cv2.CAP_PROP_HUE,
    "CAP_PROP_GAIN": cv2.CAP_PROP_GAIN,
    "CAP_PROP_EXPOSURE": cv2.CAP_PROP_EXPOSURE,
    "CAP_PROP_FOURCC": cv2.CAP_PROP_FOURCC,
    "CAP_PROP_AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
    "CAP_PROP_AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
    "CAP_PROP_BUFFERSIZE": cv2.CAP_PROP_BUFFERSIZE,
    "CAP_PROP_BACKLIGHT": 32,  # Not always available
    "CAP_PROP_TEMPERATURE": 23,  # Not always available
}

print("Camera properties:")
for name, prop_id in props.items():
    value = cap.get(prop_id)
    if value == -1 or value == 0:
        print(f"{name}: Not supported or 0")
    else:
        print(f"{name}: {value}")

cap.release()


exit

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # If frame is read correctly, ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Display the resulting frame
    cv2.imshow('Camera', frame)

    # Exit with 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()