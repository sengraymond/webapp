# Use an official Python runtime as a parent image
FROM python:3.14-alpine

# Set the working directory
WORKDIR /webapp

# Copy the application source code, templates, and static files
COPY flask_app.py /webapp
COPY static /webapp/static/
COPY templates /webapp/templates/
COPY requirements.txt /webapp/requirements.txt

# Create a system group and user with a high UID/GID
RUN addgroup -g 10001 appgroup && \
    adduser -u 10001 -G appgroup -D -h /home/appuser appuser

# Grant ownership and explicit read/write permissions to appuser
RUN chown -R appuser:appgroup /webapp && \
    chmod -R 755 /webapp

# Switch to the non-root user
USER appuser

# Install Python packages required for the application
RUN pip install --no-cache-dir -r /webapp/requirements.txt

# Set the environment PATH (appends the new path to existing system paths)
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Run Flask
ENV FLASK_APP=/webapp/flask_app.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=3000", "--cert=/webapp/cert.pem", "--key=/webapp/key.pem"]

# Make HTTPS port 3000 available to the world outside this container
EXPOSE 3000


