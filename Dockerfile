FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN git config --global user.name "Gemini Agent"
RUN git config --global user.email "agent@criptopnz.com"

WORKDIR /app
COPY . .
RUN chmod +x start.sh agent.py

CMD ["/app/start.sh"]
