FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY quant_bitcoin ./quant_bitcoin
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/quant_backtest_api ./backend/quant_backtest_api

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir . \
    && python -m pip install --no-cache-dir ./backend

EXPOSE 8000

CMD ["uvicorn", "backend.quant_backtest_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
