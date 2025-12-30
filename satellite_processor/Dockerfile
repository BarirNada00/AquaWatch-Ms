FROM python:3.10-slim

WORKDIR /app

RUN echo 'deb http://deb.debian.org/debian bullseye-backports main' >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y -t bullseye-backports gdal-bin libgdal-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt flask

COPY . .

EXPOSE 5000

# Force rebuild trigger
RUN echo "Rebuild trigger 2"

CMD ["python", "api.py"]
