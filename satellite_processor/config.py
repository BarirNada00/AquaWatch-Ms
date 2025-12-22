import os

# --- Sentinel Hub ---
SENTINELHUB_CLIENT_ID: str = os.getenv("SENTINELHUB_CLIENT_ID", "6b5b432e-ab58-40d0-94c1-63d6a7dadddf")
SENTINELHUB_CLIENT_SECRET: str = os.getenv("SENTINELHUB_CLIENT_SECRET", "TJGJAzsKQ004wjrpTbbtzjxHy1yDF0un")

# --- MinIO ---
MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "satellite-data")

# --- Satellite ---
PROCESS_INTERVAL_HOURS: int = int(os.getenv("PROCESS_INTERVAL_HOURS", 24))