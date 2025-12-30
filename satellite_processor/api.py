import json
import logging
import os
from flask import Flask, jsonify
from flask_cors import CORS
from py_eureka_client.eureka_client import EurekaClient

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize Eureka client
eureka_client = EurekaClient(
    app_name='satellite-processor',
    eureka_server="http://eureka-server:8761/eureka/",
    instance_host='satellite-processor',
    instance_port=5000
)
eureka_client.register()

@app.route('/satellite_processor/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
