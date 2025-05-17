from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse
from PIL import Image
import pytesseract
import io
import cv2
import numpy as np

app = FastAPI()


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    Tiền xử lý ảnh: chuyển grayscale, threshold và resize lên 3x để OCR chính xác hơn
    """
    img_cv = np.array(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

    # Resize lên 3 lần
    thresh = cv2.resize(thresh, (thresh.shape[1] * 3, thresh.shape[0] * 3), interpolation=cv2.INTER_LINEAR)
    return Image.fromarray(thresh)


def crop_captcha_region(image: Image.Image) -> Image.Image:
    """
    Cắt vùng chứa CAPTCHA theo tỉ lệ ảnh — hoạt động trên mọi độ phân giải
    """
    width, height = image.size
    x1 = int(width * 0.605)
    y1 = int(height * 0.567)
    x2 = int(width * 0.70)
    y2 = int(height * 0.588)
    return image.crop((x1, y1, x2, y2))


@app.post("/extract-all-text", response_class=PlainTextResponse)
async def extract_all_text(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # OCR toàn ảnh bằng tiếng Việt
        full_text = pytesseract.image_to_string(image, lang="vie", config="--psm 6")
        return full_text.strip() if full_text.strip() else "Không phát hiện văn bản nào"
    except Exception as e:
        return PlainTextResponse(f"Lỗi: {str(e)}", status_code=500)


@app.post("/extract-captcha")
async def extract_captcha(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        original_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Cắt và xử lý ảnh vùng captcha
        captcha_img = crop_captcha_region(original_image)
        processed = preprocess_for_ocr(captcha_img)

        # OCR bằng Tesseract với cấu hình tối ưu
        captcha_text = pytesseract.image_to_string(
            processed,
            lang="eng",  # Tiếng Anh vì chỉ nhận ký tự
            config='--psm 10 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ).strip()

        return JSONResponse(content={
            "captcha_text": captcha_text,
            "image_size": original_image.size
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
