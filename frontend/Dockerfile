# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy only package.json first to leverage Docker cache
COPY package.json ./

# Install dependencies, ignoring peer conflicts
RUN npm install --legacy-peer-deps

# Copy the rest of the code
COPY . .
RUN npm run build

# Serve with nginx
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
