FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "from transformers import GPT2LMHeadModel, GPT2TokenizerFast; GPT2TokenizerFast.from_pretrained('gpt2'); GPT2LMHeadModel.from_pretrained('gpt2')"

RUN mkdir -p /app/logs /app/data

EXPOSE 8000

CMD ["gunicorn", "--workers", "1", "--threads", "2", "--bind", "0.0.0.0:8000", "app:app"]
