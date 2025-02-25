FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY . /app/
COPY staticfiles/ /app/staticfiles/
RUN python manage.py collectstatic --noinput

RUN chmod 644 /app/uwsgi.ini && \
    chown -R root:root /app

RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uwsgi", "--ini", "uwsgi.ini"]
