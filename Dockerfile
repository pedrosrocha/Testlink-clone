# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install pipenv
RUN pip install pipenv

COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy 
# RUN pipenv install --system --deploy --ignore-pipfile

# Copy the rest of the application's code to the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
