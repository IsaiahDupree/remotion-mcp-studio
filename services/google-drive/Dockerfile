FROM python:3.11-slim

WORKDIR /srv

# Install Google API Client, Flask, and OAuth libraries
RUN pip install flask google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

# Create directories for credentials and tokens
RUN mkdir -p /srv/credentials

# Copy application code
COPY app.py .

# Expose the Flask port
EXPOSE 5000

# Set environment variables
ENV OAUTHLIB_RELAX_TOKEN_SCOPE=1

# Run the Flask application
CMD ["python", "app.py"]
