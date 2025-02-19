FROM python:3.11-slim

WORKDIR /backend

RUN apt-get update && apt-get install -y build-essential gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="."
ENV FLASK_APP=src/app.py
EXPOSE 8080 

CMD ["sh", "-c", "python -u -m flask run --host=0.0.0.0 --port=${PORT:-8080}"]
