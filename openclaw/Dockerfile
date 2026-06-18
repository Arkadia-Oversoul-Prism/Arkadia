FROM node:22-slim

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY gateway.js config.json ./

EXPOSE 3000

CMD ["node", "gateway.js"]
