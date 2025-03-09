import cv2
import pytesseract
import requests
import json
import base64
from dotenv import load_dotenv
import os
from pathlib import Path
import argparse

# Load environment variables
load_dotenv(dotenv_path=Path('../.env'))

class DirectOcr:
    def __init__(self, image_dir, use_google_vision=False):
        self.image_dir = Path(image_dir)
        self.use_google_vision = use_google_vision
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

        # Create output directory based on the input directory name
        self.output_dir = Path("translated") / self.image_dir.name
        os.makedirs(self.output_dir, exist_ok=True)

    def preprocess_image(self, image_path):
        """Preprocess the image for better OCR results."""
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Error: Could not load image {image_path}. Please check the file path.")
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        binary = cv2.adaptiveThreshold(enhanced, 245, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5)

        return binary

    def extract_text_with_tesseract(self, image):
        """Extract text using Tesseract OCR."""
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

    def extract_text_with_google_vision(self, image_path):
        """Extract text using Google Cloud Vision API."""
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            encoded_image = base64.b64encode(content).decode('utf-8')

            payload = {
                "requests": [
                    {
                        "image": {"content": encoded_image},
                        "features": [{"type": "TEXT_DETECTION"}],
                    }
                ]
            }

            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_api_key}"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(payload), headers=headers)

            if response.status_code == 200:
                result = response.json()
                if 'responses' in result and len(result['responses']) > 0:
                    texts = result['responses'][0].get('textAnnotations', [])
                    if texts:
                        return texts[0]['description']  # Return the extracted text
                    else:
                        print("No text was extracted.")
                        return None
                else:
                    print("No text was extracted.")
                    return None
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"An error occurred with Google Cloud Vision: {e}")
            return None

    def process_image(self, image_path):
        """Process a single image and save the extracted text."""
        print(f"Processing image: {image_path}")

        if self.use_google_vision:
            text = self.extract_text_with_google_vision(image_path)
        else:
            binary_image = self.preprocess_image(image_path)
            if binary_image is not None:
                text = self.extract_text_with_tesseract(binary_image)

        if text:
            # Save the extracted text with the same name as the image
            image_name = Path(image_path).stem
            output_file = self.output_dir / f"{image_name}.txt"
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(text)
            print(f"Saved extracted text to {output_file}")

    def process_directory(self):
        """Process all images in the directory."""
        if not self.image_dir.is_dir():
            print(f"Error: {self.image_dir} is not a valid directory.")
            return

        for image_path in self.image_dir.glob("*.*"):
            if image_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                self.process_image(image_path)


if __name__ == "__main__":
    image_book_directory = "resources/como_reconocer_el_arte_del_modernismo" # Default value

    parser = argparse.ArgumentParser(description="Extract text from images in a directory.")
    parser.add_argument(
        "--image_dir", 
        type=str,
        default=image_book_directory,
        required=False, 
        help="Path to the directory containing images."
    )
    parser.add_argument(
        "--use_google_vision", 
        action="store_true", 
        default=False,
        help="Use Google Cloud Vision API for text extraction."
    )
    args = parser.parse_args()

    extractor = DirectOcr(image_dir=args.image_dir, use_google_vision=args.use_google_vision)

    extractor.process_directory()