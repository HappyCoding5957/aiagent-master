FROM python:3.11-slim

WORKDIR /app

# Tesseract OCR（正式部署時可用；demo 環境沒裝也不影響啟動，MockOCR 會自動接手）
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-chi-tra \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8420
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8420"]
