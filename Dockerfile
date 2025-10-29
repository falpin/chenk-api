FROM python:3.10-slim

WORKDIR /app

# Установка OpenVPN
RUN apt-get update && \
    apt-get install -y openvpn curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn && \
    find . -name "__pycache__" -exec rm -rf {} + && \
    find . -name "*.pyc" -delete

# Копируем .ovpn файл и entrypoint.sh
COPY your-config.ovpn /etc/openvpn/client.ovpn
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY . .

RUN find . -name "__pycache__" -exec rm -rf {} + \
    && find . -name "*.pyc" -delete

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "server:app"]