FROM python:3.9-slim

WORKDIR /app

COPY backend/foodgram/requirements.txt .

RUN pip3 install -r /app/requirements.txt --no-cache-dir

COPY backend/foodgram/ /app

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]
