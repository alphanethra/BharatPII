import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Change filename to any image you have
image = Image.open("test_image.jpeg")

text = pytesseract.image_to_string(image, lang="eng+kan+tam+tel+hin")

print("Extracted Text:")
print(text)
