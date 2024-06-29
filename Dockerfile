# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create the uploads directory if it doesn't exist
RUN mkdir -p /app/uploads

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy model
RUN python -m spacy download fr_core_news_sm

# Install NLTK data
RUN python -m nltk.downloader punkt stopwords

# Expose port 5000 for the Flask app
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
