FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY *.js ./

EXPOSE 8002

CMD ["npm", "start"]
