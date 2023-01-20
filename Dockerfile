FROM python:3

WORKDIR /opt/civviebot
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn pg8000