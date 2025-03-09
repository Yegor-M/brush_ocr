import cv2
import numpy as np
import pytesseract
import argparse

class BrushOCR:
    def __init__(self, image_path, output_file='extracted_text.txt', brush_size=50):
        self.image_path = image_path
        self.output_file = output_file
        self.brush_size = brush_size

        # Initialize global variables
        self.drawing = False  # True if mouse is pressed
        self.ix, self.iy = -1, -1  # Initial coordinates of the brush
        self.image = None  # Original image
        self.clone = None  # Copy of the image for drawing
        self.mask = None  # Mask to store highlighted regions

    def draw_brush(self, event, x, y, flags, param):
        """Handle mouse events for brush selection."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                cv2.line(self.clone, (self.ix, self.iy), (x, y), (0, 255, 0), self.brush_size)
                cv2.line(self.mask, (self.ix, self.iy), (x, y), 255, self.brush_size)
                self.ix, self.iy = x, y

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            cv2.line(self.clone, (self.ix, self.iy), (x, y), (0, 255, 0), self.brush_size)
            cv2.line(self.mask, (self.ix, self.iy), (x, y), 255, self.brush_size)

    def preprocess_image(self, image):
        """Preprocess the image for better OCR results."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        binary = cv2.adaptiveThreshold(enhanced, 245, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5)
        return binary

    def extract_text(self, image):
        """Extract text from the image using Tesseract OCR."""
        try:
            text = pytesseract.image_to_string(image, lang='spa', config='--psm 6')
            if text.strip():
                return text
            else:
                print("No text was extracted.")
                return None
        except pytesseract.TesseractNotFoundError:
            print("Error: Tesseract is not installed or not in your PATH.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def run(self):
        """Run the BrushOCR tool."""
        # Load the image
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            print("Error: Could not load image. Please check the file path.")
            return

        self.clone = self.image.copy()
        self.mask = np.zeros(self.image.shape[:2], dtype=np.uint8)

        # Set up the window and mouse callback
        cv2.namedWindow('Highlight Text')
        cv2.setMouseCallback('Highlight Text', self.draw_brush)

        # Main loop for brush selection
        while True:
            cv2.imshow('Highlight Text', self.clone)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('r'):  # Reset brush
                self.clone = self.image.copy()
                self.mask = np.zeros(self.image.shape[:2], dtype=np.uint8)

            elif key == ord('q'):  # Quit
                break

        cv2.destroyAllWindows()

        # Process the highlighted region
        if np.any(self.mask):
            highlighted = cv2.bitwise_and(self.image, self.image, mask=self.mask)
            gray_highlighted = cv2.cvtColor(highlighted, cv2.COLOR_BGR2GRAY)

            # Preprocess the highlighted region
            binary_highlighted = self.preprocess_image(highlighted)

            # Show the highlighted and processed regions
            cv2.imshow('Highlighted Region', highlighted)
            cv2.imshow('Processed Region', binary_highlighted)
            cv2.waitKey(0)

            # Extract text from the processed region
            text = self.extract_text(binary_highlighted)
            if text:
                with open(self.output_file, 'w', encoding='utf-8') as file:
                    file.write(text)
                    print(f"Saved extracted text to {self.output_file}")

            cv2.destroyAllWindows()
        else:
            print("No region was highlighted.")


if __name__ == "__main__":
    image_path = 'lib/introduction_page.jpeg'
    parser = argparse.ArgumentParser(description="Extract text from images in a directory.")
    parser.add_argument(
        "--image_path", 
        type=str,
        default=image_path,
        required=False, 
        help="Path to the directory containing images."
    )
    args = parser.parse_args()

    brush_ocr = BrushOCR(image_path=args.image_path)
    brush_ocr.run()