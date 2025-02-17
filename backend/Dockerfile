FROM python:3.9-slim

WORKDIR /backend

RUN apt-get update && apt-get install -y build-essential gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask google-auth google-auth-oauthlib google-auth-httplib2 requests PyStemmer google-cloud-secret-manager

COPY . /backend

ENV PYTHONPATH="/backend"
EXPOSE 8080
ENV FLASK_APP=src/api/users.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
