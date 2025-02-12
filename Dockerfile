# Use an official Python runtime as the base image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY app/requirements.txt /app/requirements.txt

# Install any dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY app/ /app/

# Expose the port the app will run on
EXPOSE 5000

# Run the Flask app when the container starts
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
