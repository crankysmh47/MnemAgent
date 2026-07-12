FROM node:20-alpine
WORKDIR /runner
RUN addgroup -S judge && adduser -S -G judge -u 10001 judge
COPY package.json ./
COPY command-policy.js patch-policy.js runner.js ./
USER judge
ENTRYPOINT ["node", "runner.js"]
