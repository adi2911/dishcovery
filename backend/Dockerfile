FROM python:3.11-slim

WORKDIR /backend

RUN apt-get update && apt-get install -y build-essential gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="."
EXPOSE 8081
ENV FLASK_APP=src/api/users.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=8081"]
