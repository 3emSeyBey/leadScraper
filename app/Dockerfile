# Start with the FastAPI Uvicorn image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

# Install necessary dependencies for Playwright and browser rendering in Docker
RUN apt-get update -y && \
    apt-get install -y wget gnupg xvfb libnss3 libxss1 libasound2 fonts-noto-color-emoji x11-apps && \
    pip install playwright motor python-dotenv && \
    playwright install --with-deps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the FastAPI application code
COPY ./ /app

# Set the working directory
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD Xvfb :99 -screen 0 1024x768x16 & python3 main.py