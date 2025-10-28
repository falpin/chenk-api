FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y openvpn curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn && \
    find . -name "__pycache__" -exec rm -rf {} + && \
    find . -name "*.pyc" -delete

COPY . .

RUN echo '${VPN_USERNAME}' > /app/vpn-credentials.txt && \
    echo '${VPN_PASSWORD}' >> /app/vpn-credentials.txt

COPY openvpn.conf /etc/openvpn/config.ovpn

CMD sh -c 'openvpn --config /etc/openvpn/config.ovpn --auth-user-pass /app/vpn-credentials.txt --daemon && sleep 15 && exec gunicorn --config gunicorn.conf.py server:app'