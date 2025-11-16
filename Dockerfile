# Arkana Rasa cloud container

FROM rasa/rasa:3.6.20-full

# Switch to root so we can adjust permissions
USER root

WORKDIR /app

# Copy the Rasa project into /app
COPY arkana_rasa/ ./

# Give ownership of /app to the Rasa runtime user (1001)
RUN chown -R 1001:1001 /app

# Switch back to the Rasa user
USER 1001

# Train the model at build time
RUN rasa train

# Default port (Render sets PORT, but we also align with 5005)
ENV PORT=5005
EXPOSE 5005

# Start Rasa with API + open CORS
CMD ["run", "--enable-api", "--cors", "*", "--port", "5005"]
