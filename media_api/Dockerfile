FROM python:3.11-slim

WORKDIR /app

# Copy API code into container
COPY media_api.py /app/

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic

EXPOSE 8700

CMD ["uvicorn", "media_api:app", "--host", "0.0.0.0", "--port", "8700"]
