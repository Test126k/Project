# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the bot script into the container
COPY bot.py .

# Start the bot
CMD ["python", "bot.py"]
