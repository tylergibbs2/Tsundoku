FROM python:3.11-slim

# bencodepy is only needed to *decode* real torrents in the mirror; the
# tracker deliberately stays on the standard library.
RUN pip install --no-cache-dir bencodepy==0.9.5

WORKDIR /app
COPY app/ /app/

# No CMD: compose picks tracker.py or mirror.py per service.
