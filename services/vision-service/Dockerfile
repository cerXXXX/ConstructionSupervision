# Контекст сборки — корень репозитория: сервису нужен packages/py-common.
# Образ пока без CUDA и без весов: слой с PyTorch весит 6–8 ГБ и собирается
# десятками минут, поэтому он появится вместе с самим распознаванием (B-04).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY packages/py-common /app/packages/py-common
RUN pip install /app/packages/py-common

COPY services/vision-service/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY services/vision-service /app/services/vision-service
WORKDIR /app/services/vision-service

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
