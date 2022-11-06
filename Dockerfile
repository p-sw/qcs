FROM python:3.10.7

RUN . venv/bin/activate
RUN pip install -r requirements.txt

WORKDIR /app

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]