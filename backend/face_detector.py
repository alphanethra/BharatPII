import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image
import io


def blur_faces_image(image_bytes):
    """
    Detect and blur faces in an image.
    Returns blurred image bytes and number of faces detected.
    """

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return image_bytes, 0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(60, 60)
    )

    for (x, y, w, h) in faces:
        face_region = img[y:y+h, x:x+w]
        blurred = cv2.GaussianBlur(face_region, (99, 99), 30)
        img[y:y+h, x:x+w] = blurred

    _, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes(), len(faces)


def blur_faces_pdf(pdf_bytes, poppler_path):
    """
    Convert PDF pages to images, blur faces, rebuild PDF.
    """

    pages = convert_from_bytes(pdf_bytes, poppler_path=poppler_path)
    blurred_pages = []
    total_faces = 0

    for page in pages:
        img_bytes = io.BytesIO()
        page.save(img_bytes, format="JPEG")
        blurred_img_bytes, face_count = blur_faces_image(img_bytes.getvalue())
        total_faces += face_count

        blurred_img = Image.open(io.BytesIO(blurred_img_bytes))
        blurred_pages.append(blurred_img)

    output_pdf = io.BytesIO()
    blurred_pages[0].save(
        output_pdf,
        save_all=True,
        append_images=blurred_pages[1:],
        format="PDF"
    )

    return output_pdf.getvalue(), total_faces