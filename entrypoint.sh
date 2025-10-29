#!/bin/bash

# Подгружаем .env файл
set -a
source .env
set +a

# Создаем временный файл с логином и паролем
echo "$VPN_USERNAME" > /tmp/vpn-credentials
echo "$VPN_PASSWORD" >> /tmp/vpn-credentials

# Запускаем OpenVPN в фоне с отключенной проверкой сертификата
openvpn --client \
  --dev tun \
  --proto udp \
  --remote vpn.chenk.ru 1194 \
  --auth-user-pass /tmp/vpn-credentials \
  --cipher AES-256-GCM \
  --verb 3 \
  --tls-verify none \
  --verify-x509-name none &

# Ждем немного, чтобы VPN подключился
sleep 10

# Запускаем основную команду (gunicorn)
exec "$@"