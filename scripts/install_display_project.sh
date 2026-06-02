#!/usr/bin/env bash
# install_display_project.sh
# Instala el proyecto multimodo en la Raspberry Pi.

set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
  echo "Ejecuta con sudo:"
  echo "  sudo ./scripts/install_display_project.sh"
  exit 1
fi

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Copiando archivos Python en /home/raspberry..."
cp "$PACKAGE_DIR/src/ble_server.py" /home/raspberry/ble_server.py
cp "$PACKAGE_DIR/src/web_poll_display.py" /home/raspberry/web_poll_display.py
cp "$PACKAGE_DIR/src/gpio_shutdown_watch.py" /home/raspberry/gpio_shutdown_watch.py
cp "$PACKAGE_DIR/src/test_lcd.py" /home/raspberry/test_lcd.py

echo "Copiando scripts..."
cp "$PACKAGE_DIR/scripts/switch_display_mode.sh" /home/raspberry/switch_display_mode.sh
cp "$PACKAGE_DIR/scripts/connect_wifi.sh" /home/raspberry/connect_wifi.sh
chmod +x /home/raspberry/switch_display_mode.sh
chmod +x /home/raspberry/connect_wifi.sh

echo "Copiando configuraciones de ejemplo si no existen..."
if [ ! -f /home/raspberry/web_config.json ]; then
  cp "$PACKAGE_DIR/config/web_config.example.json" /home/raspberry/web_config.json
  chown raspberry:raspberry /home/raspberry/web_config.json
fi

if [ ! -f /home/raspberry/wifi_command_config.json ]; then
  cp "$PACKAGE_DIR/config/wifi_command_config.example.json" /home/raspberry/wifi_command_config.json
  chown raspberry:raspberry /home/raspberry/wifi_command_config.json
fi

if [ ! -f /home/raspberry/gpio_shutdown_config.json ]; then
  cp "$PACKAGE_DIR/config/gpio_shutdown_config.example.json" /home/raspberry/gpio_shutdown_config.json
fi

echo "Instalando servicios systemd..."
cp "$PACKAGE_DIR/systemd/bt-agent-auto.service" /etc/systemd/system/bt-agent-auto.service
cp "$PACKAGE_DIR/systemd/ble-server.service" /etc/systemd/system/ble-server.service
cp "$PACKAGE_DIR/systemd/web-display.service" /etc/systemd/system/web-display.service
cp "$PACKAGE_DIR/systemd/gpio-shutdown.service" /etc/systemd/system/gpio-shutdown.service
cp "$PACKAGE_DIR/systemd/display-mode-switch@.service" /etc/systemd/system/display-mode-switch@.service

echo "Configurando permisos sudo limitados..."
cat > /etc/sudoers.d/display_modes <<'EOF'
raspberry ALL=(root) NOPASSWD: /home/raspberry/switch_display_mode.sh
raspberry ALL=(root) NOPASSWD: /usr/bin/systemctl start display-mode-switch@web.service
raspberry ALL=(root) NOPASSWD: /usr/bin/systemctl start display-mode-switch@ble.service
EOF

cat > /etc/sudoers.d/display_wifi <<'EOF'
raspberry ALL=(root) NOPASSWD: /home/raspberry/connect_wifi.sh
EOF

chmod 440 /etc/sudoers.d/display_modes /etc/sudoers.d/display_wifi
visudo -cf /etc/sudoers.d/display_modes >/dev/null
visudo -cf /etc/sudoers.d/display_wifi >/dev/null

echo "Recargando systemd..."
systemctl daemon-reload

echo ""
echo "Instalación terminada."
echo ""
echo "Edita antes de iniciar modo web:"
echo "  nano /home/raspberry/web_config.json"
echo ""
echo "Edita antes de usar comando WiFi por BLE:"
echo "  nano /home/raspberry/wifi_command_config.json"
echo ""
echo "Activar modo web:"
echo "  sudo /home/raspberry/switch_display_mode.sh web"
echo ""
echo "Activar modo BLE:"
echo "  sudo /home/raspberry/switch_display_mode.sh ble"
