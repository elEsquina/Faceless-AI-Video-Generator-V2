FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates fonts-liberation fonts-dejavu-core \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libx11-6 libxcomposite1 \
  libxdamage1 libxrandr2 libgbm1 libasound2 libxkbcommon0 libxfixes3 \
  libdrm2 libdbus-1-3 libpango-1.0-0 libcairo2 \
  libatspi2.0-0 libglib2.0-0 chromium \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY remotion/package.json ./package.json
RUN npm install --no-audit --no-fund
COPY remotion/src ./src
