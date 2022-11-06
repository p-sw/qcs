FROM python:3.10.7

WORKDIR /app

COPY . .

RUN . venv/bin/activate && pip install -r requirements.txt

CMD . venv/bin/activate && gunicorn --bind 0.0.0.0:5001 app:app