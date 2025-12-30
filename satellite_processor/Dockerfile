FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gdal-bin libgdal-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt flask

COPY . .

EXPOSE 5000

# Force rebuild trigger
RUN echo "Rebuild trigger 2"

CMD ["python", "api.py"]
