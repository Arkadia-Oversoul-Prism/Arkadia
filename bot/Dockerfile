FROM node:20-slim

WORKDIR /app

COPY bot/package.json ./
RUN npm install --production

COPY bot/telegram-bot.mjs .

CMD ["node", "telegram-bot.mjs"]
