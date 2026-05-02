FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# Install system dependencies for OCR and processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models to avoid cold starts on first request
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
    SentenceTransformer('BAAI/bge-m3'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
    from transformers import pipeline; pipeline('text2text-generation', model='google/flan-t5-base')"

# Pre-download PaddleOCR models (det, rec, cls for English)
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='en', show_log=False)"

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
