FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD ["/bin/bash", "-c", "python3 manage.py makemigrations users tags recipes ingredients && python3 manage.py migrate && gunicorn --bind 0.0.0.0:8000 backend.wsgi"]