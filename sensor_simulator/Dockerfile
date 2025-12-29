FROM node:20-slim

WORKDIR /app

COPY sensor_simulator/package*.json ./
RUN npm install

COPY sensor_simulator/*.js ./

EXPOSE 8002

CMD ["npm", "start"]
