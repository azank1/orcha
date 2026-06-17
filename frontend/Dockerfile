FROM node:20-slim AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_GATEWAY_URL=/api
ARG VITE_SANDBOX_MODE=false
ENV VITE_GATEWAY_URL=${VITE_GATEWAY_URL}
ENV VITE_SANDBOX_MODE=${VITE_SANDBOX_MODE}
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY deploy/sandbox/frontend-nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
