FROM node:20-alpine
RUN apk add --no-cache git docker-cli && addgroup -S broker && adduser -S -G broker -u 10002 broker
WORKDIR /app
COPY workspace-broker/package.json ./
COPY workspace-broker/src ./src
COPY workspace-runner/patch-policy.js /workspace-runner/patch-policy.js
RUN mkdir -p /workspaces && chown -R broker:broker /workspaces
USER broker
ENTRYPOINT ["node", "src/index.js"]
