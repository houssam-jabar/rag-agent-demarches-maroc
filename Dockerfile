FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-base')"

COPY api/ ./api/
COPY rag/ ./rag/

EXPOSE 8000

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
