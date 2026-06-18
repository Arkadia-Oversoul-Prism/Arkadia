FROM node:22-alpine

# Install OpenClaw globally
RUN npm install -g openclaw@latest

WORKDIR /app

# Copy config
COPY config.json .

# Expose webhook port
EXPOSE 3000

CMD ["openclaw", "start", "--config", "config.json"]
