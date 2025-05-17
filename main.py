from fastapi import FastAPI, UploadFile, File
from fastapi.responses import PlainTextResponse
from PIL import Image
import easyocr
import numpy as np
import io

app = FastAPI()

# Khởi tạo reader khi server start (ngôn ngữ tiếng Anh)
reader = easyocr.Reader(['en'], gpu=False)

@app.post("/extract-all-text", response_class=PlainTextResponse)
async def extract_all_text(file: UploadFile = File(...)):
    try:
        # Đọc ảnh từ file upload
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # OCR toàn ảnh bằng easyocr
        results = reader.readtext(np.array(image))

        # Ghép các đoạn văn bản lại
        extracted_text = "\n".join([item[1] for item in results])

        return extracted_text if extracted_text.strip() else "No text found"
    except Exception as e:
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)
