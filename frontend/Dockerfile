FROM node:22-alpine AS build

WORKDIR /app

COPY package.json ./
RUN sed -i \
  -e 's/"@replit\/vite-plugin-cartographer": "catalog:"/"@replit\/vite-plugin-cartographer": "0.0.1"/g' \
  -e 's/"@replit\/vite-plugin-dev-banner": "catalog:"/"@replit\/vite-plugin-dev-banner": "0.0.1"/g' \
  -e 's/"@replit\/vite-plugin-runtime-error-modal": "catalog:"/"@replit\/vite-plugin-runtime-error-modal": "0.0.1"/g' \
  -e 's/"@tailwindcss\/vite": "catalog:"/"@tailwindcss\/vite": "^4.0.0"/g' \
  -e 's/"@tanstack\/react-query": "catalog:"/"@tanstack\/react-query": "^5.62.0"/g' \
  -e 's/"@types\/node": "catalog:"/"@types\/node": "^22.10.0"/g' \
  -e 's/"@types\/react": "catalog:"/"@types\/react": "^19.0.0"/g' \
  -e 's/"@types\/react-dom": "catalog:"/"@types\/react-dom": "^19.0.0"/g' \
  -e 's/"@vitejs\/plugin-react": "catalog:"/"@vitejs\/plugin-react": "^4.3.4"/g' \
  -e 's/"class-variance-authority": "catalog:"/"class-variance-authority": "^0.7.1"/g' \
  -e 's/"clsx": "catalog:"/"clsx": "^2.1.1"/g' \
  -e 's/"framer-motion": "catalog:"/"framer-motion": "^11.15.0"/g' \
  -e 's/"lucide-react": "catalog:"/"lucide-react": "^0.468.0"/g' \
  -e 's/"react": "catalog:"/"react": "^19.0.0"/g' \
  -e 's/"react-dom": "catalog:"/"react-dom": "^19.0.0"/g' \
  -e 's/"tailwind-merge": "catalog:"/"tailwind-merge": "^2.6.0"/g' \
  -e 's/"tailwindcss": "catalog:"/"tailwindcss": "^4.0.0"/g' \
  -e 's/"vite": "catalog:"/"vite": "^6.0.0"/g' \
  -e 's/"zod": "catalog:"/"zod": "^3.24.1"/g' \
  -e 's/"@workspace\/api-client-react": "workspace:\*"/"@workspace\/api-client-react": "^1.0.0"/g' \
  package.json

RUN npm install

COPY . .

ENV PORT=80
ENV BASE_PATH=/
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist/public /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
