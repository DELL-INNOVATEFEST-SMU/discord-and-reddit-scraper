# Use JDK 17 base image
FROM openjdk:17-slim

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Download NLTK vader_lexicon (optional, only if you want VADER too)
RUN python3 -m nltk.downloader vader_lexicon

# Expose Flask port
EXPOSE 5000

# Start Flask API
CMD ["python3", "app.py"]
