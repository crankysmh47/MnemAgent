FROM node:20-alpine
LABEL org.opencontainers.image.title="MnemOS Visualizer Harness"
LABEL org.opencontainers.image.description="Memory graph visualizer and API proxy for MnemOS memory layer"
LABEL org.opencontainers.image.authors="crankysmh47"
LABEL org.opencontainers.image.source="https://github.com/crankysmh47/MnemAgent"

WORKDIR /app

COPY package*.json ./
RUN npm ci --production

COPY src/ ./src/
COPY openclaw-config/ ./openclaw-config/

EXPOSE 3000

CMD ["node", "src/index.js"]
