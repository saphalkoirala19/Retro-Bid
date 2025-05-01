# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the image
COPY . /app/

# Create scripts directory and copy the superuser script
RUN mkdir -p /app/scripts/
COPY scripts/create_superuser.py /app/scripts/

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD sh -c "python manage.py migrate && python manage.py shell < scripts/create_superuser.py && python manage.py runserver 0.0.0.0:8000" 