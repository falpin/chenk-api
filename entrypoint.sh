#!/bin/bash

# Подгружаем .env файл
set -a
source .env
set +a

# Создаем временный файл с логином и паролем
echo "$VPN_USERNAME" > /tmp/vpn-credentials
echo "$VPN_PASSWORD" >> /tmp/vpn-credentials

# Запускаем OpenVPN в фоне, используя .ovpn файл
openvpn --config /etc/openvpn/client.ovpn \
  --auth-user-pass /tmp/vpn-credentials \
  --verb 3 &

# Ждем немного, чтобы VPN подключился
sleep 10

# Запускаем основную команду (gunicorn)
exec "$@"