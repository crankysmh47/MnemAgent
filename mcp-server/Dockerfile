FROM node:24-slim
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev
COPY src ./src
ENV MCP_PORT=8001
ENV MNEMOS_URL=http://mnemos-memory:8000
EXPOSE 8001
CMD ["node", "src/index.js", "--transport", "http", "--port", "8001"]
