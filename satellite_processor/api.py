from flask import Flask, jsonify, request, Blueprint
import os
import json
import subprocess
from minio import Minio
from minio.error import S3Error
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Create a blueprint for satellite processor routes
satellite_bp = Blueprint('satellite_processor', __name__, url_prefix='/satellite_processor')

# Configuration MinIO (même que main.py)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "satellite-data")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

AOI_FOLDER = "aois"

@satellite_bp.route('/aois', methods=['GET'])
def get_aois():
    """Lister les AOI disponibles"""
    try:
        aois = []
        for file in os.listdir(AOI_FOLDER):
            if file.endswith(".geojson"):
                aois.append(os.path.splitext(file)[0])
        return jsonify(aois)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@satellite_bp.route('/process/<aoi>', methods=['POST'])
def process_aoi(aoi):
    """Déclencher le traitement d'une AOI"""
    try:
        # Vérifier si l'AOI existe
        aoi_file = f"{aoi}.geojson"
        if not os.path.exists(os.path.join(AOI_FOLDER, aoi_file)):
            return jsonify({"error": f"AOI {aoi} non trouvée"}), 404

        # Exécuter le script main.py pour cette AOI
        result = subprocess.run([
            "python", "main.py"
        ], capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode != 0:
            return jsonify({"error": f"Erreur lors du traitement: {result.stderr}"}), 500

        return jsonify({"message": f"Traitement de {aoi} déclenché avec succès"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@satellite_bp.route('/health', methods=['GET'])
def health():
    """Vérifier l'état du service"""
    print("Health endpoint called")
    return jsonify({"status": "ok"})

@satellite_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Récupérer les métriques satellitaires depuis MinIO"""
    try:
        objects = minio_client.list_objects(MINIO_BUCKET)
        metrics = []

        for obj in objects:
            if obj.object_name.endswith(".json"):
                # Télécharger et parser le JSON
                response = minio_client.get_object(MINIO_BUCKET, obj.object_name)
                data = json.loads(response.read().decode('utf-8'))
                metrics.append(data)

        return jsonify(metrics)
    except S3Error as e:
        return jsonify({"error": f"Erreur MinIO: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Register the blueprint
app.register_blueprint(satellite_bp)

if __name__ == '__main__':
    print("Starting Flask app for satellite_processor")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
