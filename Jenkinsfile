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
                echo '🔧 Nettoyage complet du workspace...'
                bat '''
                    @echo off
                    echo Nettoyage du workspace...
                    if exist .git (
                        echo Suppression du dossier .git...
                        rmdir /s /q .git 2>nul
                    )
                    for /d %%i in (*) do (
                        if "%%i" neq "." if "%%i" neq ".." (
                            echo Suppression du dossier %%i...
                            rmdir /s /q "%%i" 2>nul
                        )
                    )
                    for %%i in (*) do (
                        echo Suppression du fichier %%i...
                        del /q "%%i" 2>nul
                    )
                    echo Workspace nettoyé.
                '''
                script {
                    try {
                        echo '🔄 Tentative de checkout standard...'
                        checkout([
                            $class: 'GitSCM',
                            branches: [[name: '*/master']],
                            extensions: [
                                [$class: 'CloneOption', depth: 1, shallow: true, timeout: 30, noTags: true],
                                [$class: 'WipeWorkspace']
                            ],
                            userRemoteConfigs: [[url: 'https://github.com/BarirNada00/AquaWatch-Ms.git']]
                        ])
                        echo '✅ Checkout réussi'
                        bat 'git status'
                    } catch (Exception e) {
                        echo "❌ Erreur lors du checkout standard: ${e.getMessage()}"
                        echo '🔄 Tentative de récupération manuelle complète...'
                        bat '''
                            echo Initialisation Git manuelle...
                            git init
                            git config --global user.email "jenkins@local"
                            git config --global user.name "Jenkins CI"
                            git remote add origin https://github.com/BarirNada00/AquaWatch-Ms.git 2>nul || git remote set-url origin https://github.com/BarirNada00/AquaWatch-Ms.git
                            git fetch --depth 1 origin master
                            git checkout -b master FETCH_HEAD
                            git branch --set-upstream-to=origin/master master
                            git status
                            echo Récupération manuelle terminée.
                        '''
                    }
                }
            }
        }

        stage('Environment Setup') {
            steps {
                echo '🔧 Génération Config ULTRA-ISOLÉE...'
                // Recréation complète du fichier docker-compose pour isolation totale
                script {
                    def buildNum = BUILD_NUMBER.toInteger()
                    def eurekaPort = 18761 + buildNum
                    def timescaledbPort = 15433 + buildNum
                    def postgisPort = 15434 + buildNum
                    def mosquittoPort1 = 11883 + buildNum
                    def mosquittoPort2 = 19003 + buildNum
                    def geoserverPort = 18082 + buildNum
                    def minioPort1 = 19000 + buildNum
                    def minioPort2 = 19002 + buildNum
                    def ollamaPort = 11134 + buildNum
                    def anomalyDetectorPort = 18002 + buildNum
                    def apiServicePort = 18000 + buildNum
                    def apiSigPort = 18001 + buildNum
                    def satelliteProcessorPort = 18003 + buildNum
                    def sensorSimulatorPort = 18004 + buildNum
                    def webUnifieePort = 10080 + buildNum

                    writeFile file: 'docker-compose.ci.yml', text: """
version: '3.8'
services:
  eureka-server:
    image: steeltoeoss/eureka-server:latest
    container_name: ci-eureka-${BUILD_NUMBER}
    ports: ["${eurekaPort}:8761"]
    environment:
      - EUREKA_SERVER_HOSTNAME=eureka-server
      - EUREKA_SERVER_ENABLE_SELF_PRESERVATION=false
      - EUREKA_SERVER_PEER_NODE_CONNECT_TIMEOUT_MS=300000
      - EUREKA_SERVER_PEER_NODE_READ_TIMEOUT_MS=300000
      - EUREKA_SERVER_PEER_NODE_TOTAL_CONNECTIONS=1
      - EUREKA_SERVER_PEER_NODE_TOTAL_CONNECTIONS_PER_HOST=1
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "-", "http://localhost:8761/actuator/health"]
      interval: 10s
      timeout: 5s

  timescaledb:
    image: timescale/timescaledb:2.14.0-pg15
    container_name: ci-timescaledb-${BUILD_NUMBER}
    environment:
      POSTGRES_DB: aquawatch
      POSTGRES_USER: aquawatch
      POSTGRES_PASSWORD: example
    ports: ["${timescaledbPort}:5432"]
    volumes:
      - tsdata_ci:/var/lib/postgresql/data
      - ./api_sig/init_postgis.sql:/docker-entrypoint-initdb.d/init_postgis.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aquawatch"]
      interval: 10s
      timeout: 5s

  postgis:
    image: postgis/postgis:15-3.4
    container_name: ci-postgis-${BUILD_NUMBER}
    environment:
      POSTGRES_DB: aquawatch_gis
      POSTGRES_USER: aquawatch
      POSTGRES_PASSWORD: example
    ports: ["${postgisPort}:5432"]
    volumes:
      - postgis_data_ci:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aquawatch"]
      interval: 10s
      timeout: 5s

  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: ci-mosquitto-${BUILD_NUMBER}
    ports: ["${mosquittoPort1}:1883", "${mosquittoPort2}:9001"]
    volumes:
      - ./mosquitto_config/mosquitto.conf:/mosquitto/config/mosquitto.conf
    healthcheck:
       test: ["CMD-SHELL", "exit 0"]
       interval: 30s

  geoserver:
    image: docker.osgeo.org/geoserver:2.28.0
    container_name: ci-geoserver-${BUILD_NUMBER}
    ports: ["${geoserverPort}:8080"]
    healthcheck:
      test: ["CMD-SHELL", "exit 0"]

  minio:
    image: minio/minio:latest
    container_name: ci-minio-${BUILD_NUMBER}
    ports: ["${minioPort1}:9000", "${minioPort2}:9001"]
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD-SHELL", "exit 0"]

  ollama:
    image: ollama/ollama:latest
    container_name: ci-ollama-${BUILD_NUMBER}
    ports: ["${ollamaPort}:11434"]
    healthcheck:
      test: ["CMD-SHELL", "exit 0"]

  anomaly_detector:
    build:
      context: .
      dockerfile: anomaly_detector/Dockerfile
    container_name: ci-anomaly-detector-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
      TIMESCALEDB_DSN: postgresql://aquawatch:example@timescaledb:5432/aquawatch
    ports: ["${anomalyDetectorPort}:8001"]
    depends_on: [timescaledb, eureka-server]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  api_service:
    build: ./api_service
    container_name: ci-api-service-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
      POSTGIS_DSN: postgresql://aquawatch:example@postgis:5432/aquawatch_gis
    ports: ["${apiServicePort}:8000"]
    depends_on: [anomaly_detector, ollama]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/status"]
      interval: 10s
      timeout: 5s
      retries: 5

  api_sig:
    build: ./api-sig
    container_name: ci-api-sig-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
      TIMESCALEDB_DSN: postgresql://aquawatch:example@timescaledb:5432/aquawatch
      POSTGIS_DSN: postgresql://aquawatch:example@postgis:5432/aquawatch_gis
    ports: ["${apiSigPort}:8000"]
    depends_on: [postgis, eureka-server]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  satellite_processor:
    build: ./satellite_processor
    container_name: ci-satellite-processor-${BUILD_NUMBER}
    environment:
      EUREKA_SERVER_URL: http://eureka-server:8761/eureka/
    ports: ["${satelliteProcessorPort}:5000"]
    depends_on: [eureka-server]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/satellite_processor/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  sensor_simulator:
    build: ./sensor_simulator
    container_name: ci-sensor-simulator-${BUILD_NUMBER}
    environment:
      SENSOR_ID: sensor-01
      MQTT_BROKER_HOST: mosquitto
      MQTT_BROKER_PORT: 1883
      MQTT_TOPIC: sensors/readings
    ports: ["${sensorSimulatorPort}:8002"]
    depends_on: [anomaly_detector, mosquitto]

  web_unifiee:
    build: ./web-unifiee
    container_name: ci-web-unifiee-${BUILD_NUMBER}
    ports: ["${webUnifieePort}:80"]
    depends_on: [api_service, api_sig]

volumes:
  tsdata_ci:
  postgis_data_ci:
"""
                }
            }
        }

        stage('Docker Check') {
            steps {
                echo '🔍 Vérification de Docker...'
                script {
                    try {
                        bat 'docker --version'
                        bat 'docker info'
                        echo '✅ Docker est opérationnel'
                    } catch (Exception e) {
                        echo '❌ Docker n\'est pas accessible ou n\'est pas démarré'
                        echo '🔧 Veuillez démarrer Docker Desktop et relancer le pipeline'
                        echo '💡 Assurez-vous que Docker Desktop est en cours d\'exécution sur l\'agent Jenkins'
                        error('Docker is not accessible. Please start Docker Desktop and retry the pipeline.')
                    }
                }
            }
        }

        stage('Infrastructure') {
            steps {
                echo '🗄️ Démarrage Infrastructure...'
                script {
                    def maxRetries = 3
                    def retryCount = 0
                    def success = false

                    while (retryCount < maxRetries && !success) {
                        try {
                            echo "Tentative ${retryCount + 1}/${maxRetries} de démarrage de l'infrastructure..."
                            bat "${DOCKER_COMPOSE_CMD} up -d eureka-server timescaledb postgis mosquitto geoserver minio ollama"
                            success = true
                            echo '✅ Infrastructure démarrée avec succès'
                        } catch (Exception e) {
                            retryCount++
                            echo "❌ Échec tentative ${retryCount}: ${e.getMessage()}"
                            if (retryCount < maxRetries) {
                                echo "🔄 Nouvelle tentative dans 10 secondes..."
                                bat 'ping -n 11 127.0.0.1 > nul'
                            } else {
                                echo "❌ Toutes les tentatives ont échoué"
                                throw e
                            }
                        }
                    }
                }
                bat 'ping -n 16 127.0.0.1 > nul'
            }
        }

        stage('Sensor Simulator') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build sensor_simulator"
            }
        }

        stage('Anomaly Detector') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build anomaly_detector"
            }
        }

        stage('Satellite Processor') {
            steps {
                timeout(time: 60, unit: 'MINUTES') {
                    bat "${DOCKER_COMPOSE_CMD} up -d --build satellite_processor"
                }
            }
        }

        stage('API SIG') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build api_sig"
            }
        }

        stage('API Service') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build api_service"
            }
        }

        stage('Web Interface') {
            steps {
                bat "${DOCKER_COMPOSE_CMD} up -d --build web_unifiee"
                bat 'ping -n 11 127.0.0.1 > nul'
            }
        }

        stage('Health Checks') {
            steps {
                // Attendre que les services soient pleinement opérationnels
                bat 'ping -n 61 127.0.0.1 > nul'
                script {
                    def buildNum = BUILD_NUMBER.toInteger()
                    def apiServicePort = 18000 + buildNum
                    def apiSigPort = 18001 + buildNum
                    def anomalyDetectorPort = 18002 + buildNum
                    def satelliteProcessorPort = 18003 + buildNum
                    def eurekaPort = 18761 + buildNum

                    // Test des endpoints API avec PowerShell avec retry
                    powershell """
                        \$maxRetries = 5
                        \$retryCount = 0
                        \$allHealthy = \$false

                        while (\$retryCount -lt \$maxRetries -and -not \$allHealthy) {
                            try {
                                Write-Host "Tentative \$(\$retryCount + 1)/\$maxRetries de health checks..."
                                Invoke-WebRequest -Uri "http://localhost:${apiServicePort}/status" -Method GET -TimeoutSec 30
                                Invoke-WebRequest -Uri "http://localhost:${apiSigPort}/api/health" -Method GET -TimeoutSec 30
                                Invoke-WebRequest -Uri "http://localhost:${anomalyDetectorPort}/health" -Method GET -TimeoutSec 30
                                Invoke-WebRequest -Uri "http://localhost:${satelliteProcessorPort}/satellite_processor/health" -Method GET -TimeoutSec 30
                                Invoke-WebRequest -Uri "http://localhost:${eurekaPort}/actuator/health" -Method GET -TimeoutSec 30
                                Write-Host "✅ Tous les health checks sont passés!"
                                \$allHealthy = \$true
                            } catch {
                                \$retryCount++
                                Write-Host "❌ Health check failed (tentative \$retryCount): \$_"
                                if (\$retryCount -lt \$maxRetries) {
                                    Write-Host "🔄 Nouvelle tentative dans 30 secondes..."
                                    Start-Sleep -Seconds 30
                                } else {
                                    Write-Error "❌ Toutes les tentatives de health check ont échoué"
                                    exit 1
                                }
                            }
                        }
                    """
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
