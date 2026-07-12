FROM node:20-alpine
LABEL org.opencontainers.image.title="MnemAgent Visualizer Harness"
LABEL org.opencontainers.image.description="Memory graph visualizer and API proxy for MnemAgent memory layer"
LABEL org.opencontainers.image.authors="crankysmh47"
LABEL org.opencontainers.image.source="https://github.com/crankysmh47/MnemAgent"

WORKDIR /app

COPY package*.json ./
RUN npm ci --production
RUN npm install --global openclaw@2026.6.5

COPY src/ ./src/
COPY openclaw-config/ ./openclaw-config/

EXPOSE 3000

CMD ["node", "src/index.js"]
