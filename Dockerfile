FROM python:3.10.7

WORKDIR /app

COPY . /app/

RUN pip install -r requirements.txt

CMD gunicorn --bind 0.0.0.0:5001 app:app