FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY static/ static/
COPY app.py tts.py ./

RUN pip install --no-cache-dir uv \
    && uv pip install --system ".[deploy]"

EXPOSE 7860
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860"]
