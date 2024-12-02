FROM python:3.9
WORKDIR /app
RUN pip install gunicorn==20.1.0
COPY . ./app/
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]