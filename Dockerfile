FROM node:18

WORKDIR /app

COPY package*.json ./

RUN npm install || true

COPY . .

WORKDIR /app/my-node-app

COPY my-node-app/package*.json ./
RUN npm install

EXPOSE 8080

CMD ["node", "server.js"]
