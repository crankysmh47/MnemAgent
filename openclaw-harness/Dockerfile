FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --production

COPY src/ ./src/
COPY openclaw-config/ ./openclaw-config/

EXPOSE 3000

CMD ["node", "src/index.js"]
