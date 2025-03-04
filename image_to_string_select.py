import cv2
import numpy as np
import pytesseract

# Global variables
drawing = False  # True if mouse is pressed
ix, iy = -1, -1  # Initial coordinates of the brush
brush_size = 150  # Size of the brush
image = None  # Original image
clone = None  # Copy of the image for drawing
mask = None  # Mask to store highlighted regions

output_file = 'extracted_text.txt'

def draw_brush(event, x, y, flags, param):
    global ix, iy, drawing, clone, mask

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            cv2.line(clone, (ix, iy), (x, y), (0, 255, 0), brush_size)
            cv2.line(mask, (ix, iy), (x, y), 255, brush_size)
            ix, iy = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.line(clone, (ix, iy), (x, y), (0, 255, 0), brush_size)
        cv2.line(mask, (ix, iy), (x, y), 255, brush_size)

image_path = 'introduction_page.jpeg'
image = cv2.imread(image_path)

if image is None:
    print("Error: Could not load image. Please check the file path.")
    exit()

clone = image.copy()
mask = np.zeros(image.shape[:2], dtype=np.uint8)

cv2.namedWindow('Highlight Text')
cv2.setMouseCallback('Highlight Text', draw_brush)

while True:
    cv2.imshow('Highlight Text', clone)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('r'):
        clone = image.copy()
        mask = np.zeros(image.shape[:2], dtype=np.uint8)

    elif key == ord('q'):
        break

cv2.destroyAllWindows()

if np.any(mask):
    highlighted = cv2.bitwise_and(image, image, mask=mask)
    gray_highlighted = cv2.cvtColor(highlighted, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray_highlighted, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    binary_highlighted = cv2.adaptiveThreshold(enhanced, 245, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5)

    cv2.imshow('Highlighted Region', highlighted)
    cv2.imshow('Processed Region', binary_highlighted)
    cv2.waitKey(0)

    text = pytesseract.image_to_string(binary_highlighted, lang='spa', config='--psm 6')

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(text)
        print("Saved to " + output_file)

    cv2.destroyAllWindows()
else:
    print("No region was highlighted.")