FROM node:20-alpine as build
WORKDIR /app
COPY frontend_pro/package.json frontend_pro/package-lock.json* ./
RUN npm ci
COPY frontend_pro .
RUN npm run build
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]