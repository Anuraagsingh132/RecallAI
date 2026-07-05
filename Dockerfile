# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install all dependencies
COPY requirements-lock.txt .
# Use directly
RUN cp requirements-lock.txt reqs.txt

RUN pip install --no-cache-dir -r reqs.txt

# Remove dev dependencies explicitly
RUN pip uninstall -y pytest pytest-asyncio pytest-cov

# Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Ensure the appuser owns the app directory
RUN chown -R appuser:appuser /app

# Copy entrypoint script
COPY entrypoint.sh .
# Convert CRLF to LF just in case, and make it executable
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

# Startup command
ENTRYPOINT ["./entrypoint.sh"]
