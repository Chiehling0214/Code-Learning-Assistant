# syntax=docker/dockerfile:1

# ---- deps ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm install

# ---- dev (used by docker compose) ----
FROM node:22-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- build (production static assets) ----
FROM deps AS build
# Vite bakes VITE_* at build time — pass the real values as build args.
# In the single-VM deploy the API is same-origin behind Caddy, so the base URL
# is the relative "/api/v1".
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_FIREBASE_API_KEY=""
ARG VITE_FIREBASE_AUTH_DOMAIN=""
ARG VITE_FIREBASE_PROJECT_ID=""
ARG VITE_FIREBASE_APP_ID=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL     VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY     VITE_FIREBASE_AUTH_DOMAIN=$VITE_FIREBASE_AUTH_DOMAIN     VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID     VITE_FIREBASE_APP_ID=$VITE_FIREBASE_APP_ID
COPY . .
RUN npm run build

# ---- prod (static files served by nginx) ----
FROM nginx:alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
