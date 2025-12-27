import mqtt from "mqtt";
import dotenv from "dotenv";
import { randomFloat } from "./utils.js";

dotenv.config();

const SENSOR_ID = process.env.SENSOR_ID || "sensor-01";
const MQTT_BROKER_HOST = process.env.MQTT_BROKER_HOST || "mosquitto";
const MQTT_BROKER_PORT = process.env.MQTT_BROKER_PORT || 1883;
const MQTT_TOPIC = process.env.MQTT_TOPIC || "sensors/readings";
const INTERVAL = parseInt(process.env.READING_INTERVAL_SECONDS) || 2;

const client = mqtt.connect(`mqtt://${MQTT_BROKER_HOST}:${MQTT_BROKER_PORT}`);

client.on("connect", () => {
  console.log("Connected to MQTT broker");

  let counter = 0;
  setInterval(() => {
    const timestamp = new Date().toISOString();
    const reading = {
      timestamp,
      sensor_id: SENSOR_ID,
      latitude: randomFloat(34.0, 34.1),
      longitude: randomFloat(-6.8, -6.7),
      temperature: randomFloat(10, 35),
      pressure: randomFloat(1, 3),
      flow: randomFloat(20, 100),
      ph: randomFloat(6, 8),
      turbidity: randomFloat(0, 5),
      conductivity: randomFloat(50, 200)
    };

    // Introduce anomalies periodically
    if (counter % 40 === 0 && counter !== 0) reading.temperature += randomFloat(5, 15);
    if (counter % 30 === 0 && counter !== 0) reading.ph += randomFloat(1, 2);

    client.publish(MQTT_TOPIC, JSON.stringify(reading), { qos: 1 });
    console.log(`Published: ${JSON.stringify(reading)}`);
    counter++;
  }, INTERVAL * 1000);
});
