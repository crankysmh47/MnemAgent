FROM node:20-alpine
LABEL org.opencontainers.image.title="MnemAgent MCP Adapter (Legacy SSE)"
LABEL org.opencontainers.image.description="Legacy MCP SSE adapter for older OpenClaw versions"
LABEL org.opencontainers.image.authors="crankysmh47"
LABEL org.opencontainers.image.source="https://github.com/crankysmh47/MnemAgent"

WORKDIR /app

COPY package*.json ./
RUN npm ci --production

COPY server.js ./

EXPOSE 8001

CMD ["node", "server.js"]
