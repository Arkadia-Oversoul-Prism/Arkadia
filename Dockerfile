# Arkana Rasa cloud container

FROM rasa/rasa:3.6.20-full

# Work inside /app
WORKDIR /app

# Copy the Rasa project
COPY arkana_rasa/ ./

# Train the model at build time
RUN rasa train

# Default port (Render will override PORT env)
ENV PORT=5005

# Expose for local clarity (Render doesn’t strictly need this)
EXPOSE 5005

# Start Rasa with API + CORS open so we can talk from the web
CMD ["bash", "-c", "rasa run --enable-api --cors \"*\" -p ${PORT}"]
