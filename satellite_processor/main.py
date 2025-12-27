import json
import logging
import os
import io
from datetime import datetime

import numpy as np
from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    bbox_to_dimensions,
    BBox
)
from minio import Minio
from minio.error import S3Error

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration SentinelHub
config = SHConfig()
config.sh_client_id = os.getenv("SENTINELHUB_CLIENT_ID")
config.sh_client_secret = os.getenv("SENTINELHUB_CLIENT_SECRET")

# MinIO
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "minio:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=False
)
BUCKET_NAME = os.getenv("MINIO_BUCKET", "satellite-data")
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)

AOI_FOLDER = "aois"


def load_geojson(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    coords = data["features"][0]["geometry"]["coordinates"][0]
    flat = [tuple(c) for c in coords]

    lons = [c[0] for c in flat]
    lats = [c[1] for c in flat]

    bbox = BBox(bbox=[min(lons), min(lats), max(lons), max(lats)], crs="EPSG:4326")
    return bbox


def download_satellite_image(bbox):
    resolution = 10
    size = bbox_to_dimensions(bbox, resolution=resolution)

    request = SentinelHubRequest(
        data_folder="data",
        evalscript="""
            // Retourner 4 bandes : B02 (bleu), B03 (vert), B08 (NIR), B04 (rouge)
            return [B02, B03, B08, B04];
        """,
        input_data=[SentinelHubRequest.input_data(DataCollection.SENTINEL2_L2A)],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=config,
    )

    result = request.get_data()[0]  # matrice numpy
    logger.info(f"Image téléchargée : {result.shape}")

    return result


def compute_indexes(image):
    B02 = image[:, :, 0].astype(np.float32)
    B03 = image[:, :, 1].astype(np.float32)
    B08 = image[:, :, 2].astype(np.float32)
    B04 = image[:, :, 3].astype(np.float32)

    ndwi = (B03 - B08) / (B03 + B08 + 1e-6)
    turbidity = 255 - B03
    chlorophyll = B04 - B02

    return {
        "ndwi_mean": float(np.nanmean(ndwi)),
        "turbidity_mean": float(np.nanmean(turbidity)),
        "chlorophyll_mean": float(np.nanmean(chlorophyll)),
    }


def process_aoi(aoi_path):
    try:
        logger.info(f"Chargement de {aoi_path}")
        bbox = load_geojson(aoi_path)
        image = download_satellite_image(bbox)
        metrics = compute_indexes(image)

        output = {
            "aoi": os.path.basename(aoi_path),
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
        }

        # Envoyer le résultat dans MinIO
        json_bytes = json.dumps(output, indent=4).encode("utf-8")
        object_name = f"{os.path.splitext(os.path.basename(aoi_path))[0]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"

        try:
            minio_client.put_object(
                BUCKET_NAME,
                object_name,
                data=io.BytesIO(json_bytes),  # Correct: utiliser BytesIO
                length=len(json_bytes),
                content_type="application/json"
            )
            logger.info(f"Résultat envoyé dans MinIO : {object_name}")
        except S3Error as e:
            logger.error(f"Erreur MinIO : {e}")

        return output

    except Exception as e:
        logger.error(f"Erreur lors du traitement de {aoi_path}: {e}")
        return None


def main():
    results = []
    for file in os.listdir(AOI_FOLDER):
        if file.endswith(".geojson"):
            output = process_aoi(os.path.join(AOI_FOLDER, file))
            if output:
                results.append(output)

    # Sauvegarde locale (optionnelle)
    with open("satellite_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    logger.info("Traitement terminé avec succès")


if __name__ == "__main__":
    main()
