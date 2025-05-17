FROM python:3.10-slim

# Cài các gói hệ thống cần thiết (gồm cả libGL và tesseract)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    && apt-get clean

# Tạo thư mục làm việc
WORKDIR /app

# Copy project vào container
COPY . .

# Cài thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Chạy app FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
