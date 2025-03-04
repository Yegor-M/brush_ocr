import cv2
import pytesseract

output_file = 'extracted_text.txt'
img_path = 'introduction_page.jpeg'


image = cv2.imread(img_path)
if image is None:
    print("Error: Could not load image. Please check the file path.")
    exit()

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

blurred = cv2.GaussianBlur(gray, (3, 3), 0)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(blurred)

binary = cv2.adaptiveThreshold(enhanced, 245, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5)

cv2.imshow('Binary Image', binary)
cv2.waitKey(0)
cv2.imwrite('binary_image.png', binary)

try:
    text = pytesseract.image_to_string(binary, lang='spa', config='--psm 6')
    if text.strip():
        print("Extracted Text:")
        print(text)
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(text)
        print("Saved to " + output_file)
    else:
        print("No text was extracted.")
except pytesseract.TesseractNotFoundError:
    print("Error: Tesseract is not installed or not in your PATH.")
except Exception as e:
    print(f"An error occurred: {e}")



#cv2.destroyAllWindows()