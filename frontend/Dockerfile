FROM node:20-alpine3.22 AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html ./
COPY tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY vite.config.ts ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM node:20-alpine3.22 AS dev
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html ./
COPY tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY vite.config.ts ./
COPY public ./public
COPY src ./src

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM nginx:alpine AS runtime
WORKDIR /usr/share/nginx/html
RUN apk upgrade --no-cache

COPY --from=builder /app/dist ./
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

