FROM node:22-slim
LABEL org.opencontainers.image.title="MnemAgent MCP Server"
LABEL org.opencontainers.image.description="MCP tool surface for MnemAgent memory — 7 tools (stdio + HTTP)"
LABEL org.opencontainers.image.authors="crankysmh47"
LABEL org.opencontainers.image.source="https://github.com/crankysmh47/MnemAgent"
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev
COPY src ./src
ENV MCP_PORT=8001
ENV MNEMOS_URL=http://mnemos-memory:8000
EXPOSE 8001
HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=10s \
  CMD node -e "require('http').get('http://localhost:8001/health',(r)=>{process.exit(r.statusCode===200?0:1)})"
CMD ["node", "src/index.js", "--transport", "http", "--port", "8001"]
