FROM python:3.12-slim

LABEL maintainer="Louie Grant Prinz <@realteamprinz>"
LABEL description="prinzclaw — Truth-strike weapon system"

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data and log directories
RUN mkdir -p /app/data /app/logs

# Non-root user for security
RUN useradd -r -s /bin/false prinzclaw && \
    chown -R prinzclaw:prinzclaw /app
USER prinzclaw

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/health')" || exit 1

ENTRYPOINT ["python", "-m", "src.main"]
