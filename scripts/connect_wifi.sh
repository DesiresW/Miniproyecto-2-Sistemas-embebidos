#!/usr/bin/env bash
# connect_wifi.sh
# Recibe SSID y password por STDIN para no dejar la clave visible en logs de sudo.

set -euo pipefail

read -r SSID
read -r PASSWORD

if [ -z "$SSID" ] || [ -z "$PASSWORD" ]; then
  echo "ERROR: faltan SSID o password"
  exit 1
fi

CON_NAME="display-wifi-${SSID}"

echo "Intentando conectar a la red: $SSID"

nmcli radio wifi on
nmcli device wifi rescan >/dev/null 2>&1 || true
sleep 2

nmcli connection delete "$CON_NAME" >/dev/null 2>&1 || true

nmcli connection add type wifi ifname wlan0 con-name "$CON_NAME" ssid "$SSID"
nmcli connection modify "$CON_NAME" wifi-sec.key-mgmt wpa-psk
nmcli connection modify "$CON_NAME" wifi-sec.psk "$PASSWORD"
nmcli connection modify "$CON_NAME" connection.autoconnect yes

nmcli connection up "$CON_NAME"

echo "Conexión WiFi solicitada correctamente"
