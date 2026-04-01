FROM node:22-alpine

WORKDIR /app

# Enable legacy peer deps just in case
ENV npm_config_legacy_peer_deps=true

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000

# Run in dev mode to allow local hot-reloading
CMD ["npm", "run", "dev"]
