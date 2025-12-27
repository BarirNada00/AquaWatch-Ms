pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "aqua_ci_${BUILD_NUMBER}"
        // Utilisation UNIQUEMENT du fichier CI pour éviter toute fusion de ports
        DOCKER_COMPOSE_CMD = "docker-compose -f docker-compose.ci.yml"
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📥 Récupération du code...'
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/master']],
                    extensions: [[$class: 'CloneOption', depth: 1, shallow: true, timeout: 30, noTags: true]],
                    userRemoteConfigs: [[url: 'https://github.com/BarirNada00/AquaWatch-Ms.git']]
                ])
            }
        }

        stage('Environment Setup') {
            steps {
                echo '🔧 Génération Config ULTRA-ISOLÉE...'
                // Recréation complète du fichier docker-compose pour isolation totale
                writeFile file: 'docker-compose.ci.yml', text: """
version: '3.8'
services:
  eureka-server:
    image: steeltoeoss/eureka-server:latest
    container_name: ci-eureka-${BUILD_NUMBER}
    ports: ["18761:8761"]
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "-", "http://localhost:8761/actuator/health"]
      interval: 10s
      timeout: 5s

  timescaledb:
    image: timescale/timescaledb:latest-pg15
    container_name: ci-timescaledb-${BUILD_NUMBER}
    environment:
      POSTGRES_DB: aquawatch
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["15433:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s

  postgis:
    image: postgis/postgis:15-3.3
    container_name: ci-postgis-${BUILD_NUMBER}
    environment:
      POSTGRES_DB: aquawatch
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["15434:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s

  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: ci-mosquitto-${BUILD_NUMBER}
    ports: ["11883:1883", "19003:9001"]
    volumes:
      - ./mosquitto_config/mosquitto.conf:/mosquitto/config/mosquitto.conf
    healthcheck:
       test: ["CMD-SHELL", "exit 0"]
       interval: 30s

  geoserver:
    image: kartoza/geoserver:latest
    container_name: ci-geoserver-${BUILD_NUMBER}
    ports: ["18082:8080"]
    healthcheck:
      test: ["CMD-SHELL", "exit 0"]

  minio:
    image: minio/minio:latest
    container_name: ci-minio-${BUILD_NUMBER}
    ports: ["19000:9000", "19002:9001"]
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD-SHELL", "exit 0"]

  ollama:
    image: ollama/ollama
    container_name: ci-ollama-${BUILD_NUMBER}
    ports: ["11134:11434"]
    healthcheck:
      test: ["CMD-SHELL", "exit 0"]

  anomaly_detector:
    build: ./anomaly_detector
    container_name: ci-anomaly-detector-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
      DATABASE_URL: postgresql://postgres:postgres@timescaledb:5432/aquawatch
    ports: ["18002:8002"]
    depends_on: [timescaledb, eureka-server]

  api_service:
    build: ./api_service
    container_name: ci-api-service-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
      DATABASE_URL: postgresql://postgres:postgres@timescaledb:5432/aquawatch
    ports: ["18000:8000"]
    depends_on: [timescaledb, eureka-server]

  api_sig:
    build: ./api-sig
    container_name: ci-api-sig-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
      DATABASE_URL: postgresql://postgres:postgres@postgis:5432/aquawatch
    ports: ["18001:8001"]
    depends_on: [postgis, eureka-server]

  satellite_processor:
    build: ./satellite_processor
    container_name: ci-satellite-processor-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
    ports: ["18003:8003"]
    depends_on: [eureka-server]

  sensor_simulator:
    build: ./sensor_simulator
    container_name: ci-sensor-simulator-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
    ports: ["18004:8004"]
    depends_on: [eureka-server]

  web_unifiee:
    build: ./web-unifiee
    container_name: ci-web-unifiee-${BUILD_NUMBER}
    ports: ["10080:80"]
    depends_on: [api_service, api_sig]
"""
            }
        }

        stage('Infrastructure') {
            steps {
                echo '🗄️ Démarrage Infrastructure...'
                bat "${DOCKER_COMPOSE_CMD} up -d timescaledb postgis mosquitto geoserver minio ollama eureka-server"
                bat 'timeout /t 15 /nobreak > nul'
            }
        }

        stage('Anomaly Detector') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build anomaly_detector"
            }
        }

        stage('API Service') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build api_service"
            }
        }

        stage('API SIG') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build api_sig"
            }
        }

        stage('Satellite Processor') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build satellite_processor"
            }
        }

        stage('Sensor Simulator') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build sensor_simulator"
            }
        }

        stage('Web Interface') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build web_unifiee"
                bat 'timeout /t 10 /nobreak > nul'
            }
        }

        stage('Health Checks') {
            steps {
                script {
                    // Test des endpoints API avec PowerShell
                    powershell '''
                        try {
                            Invoke-WebRequest -Uri "http://host.docker.internal:18000/health" -Method GET -TimeoutSec 10
                            Invoke-WebRequest -Uri "http://host.docker.internal:18001/health" -Method GET -TimeoutSec 10
                            Invoke-WebRequest -Uri "http://host.docker.internal:18002/health" -Method GET -TimeoutSec 10
                            Invoke-WebRequest -Uri "http://host.docker.internal:18761" -Method GET -TimeoutSec 10
                            Write-Host "✅ Tous les health checks sont passés!"
                        } catch {
                            Write-Error "❌ Health check failed: $_"
                            exit 1
                        }
                    '''
                }
            }
        }
    }

    post {
        always {
            bat "${DOCKER_COMPOSE_CMD} down -v || exit 0"
            bat 'docker system prune -f || exit 0'
        }

        success {
            echo '🎉 Pipeline CI terminé avec succès!'
        }

        failure {
            echo '❌ Échec du pipeline CI'
        }
    }
}
