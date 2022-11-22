FROM python:3.11.0

WORKDIR /app

COPY . /app/

RUN pip install -r requirements.txt

CMD gunicorn main:app --bind 0.0.0.0:5001 --workers 2
