#!/usr/bin/env bash
# diagnostico_display.sh
# Exporta estado del sistema, código, servicios y logs sanitizados.

set -euo pipefail

TS="$(date +%Y%m%d_%H%M%S)"
OUT="/home/raspberry/diagnostico_display_$TS"

mkdir -p "$OUT"/{02_servicios_systemd,03_codigo_python,04_scripts,05_config_sanitizada,06_logs}

{
  echo "ARBOL /home/raspberry"
  find /home/raspberry -maxdepth 3 \( -name "__pycache__" -o -name "*.pyc" \) -prune -o -print | sort
  echo ""
  echo "SYSTEMD RELACIONADO"
  ls -lah /etc/systemd/system/*ble* /etc/systemd/system/*display* /etc/systemd/system/*gpio* 2>/dev/null || true
} > "$OUT/00_arbol.txt"

{
  /home/raspberry/switch_display_mode.sh status 2>&1 || true
  echo ""
  for svc in bt-agent-auto.service ble-server.service web-display.service gpio-shutdown.service; do
    echo "----- $svc -----"
    systemctl status "$svc" --no-pager -l 2>&1 || true
    echo ""
  done
} > "$OUT/01_estado_servicios.txt"

for svc in bt-agent-auto.service ble-server.service web-display.service gpio-shutdown.service display-mode-switch@.service; do
  systemctl cat "$svc" > "$OUT/02_servicios_systemd/$svc.txt" 2>/dev/null || true
done

cp /home/raspberry/ble_server.py "$OUT/03_codigo_python/" 2>/dev/null || true
cp /home/raspberry/web_poll_display.py "$OUT/03_codigo_python/" 2>/dev/null || true
cp /home/raspberry/gpio_shutdown_watch.py "$OUT/03_codigo_python/" 2>/dev/null || true
cp /home/raspberry/test_lcd.py "$OUT/03_codigo_python/" 2>/dev/null || true
cp /home/raspberry/switch_display_mode.sh "$OUT/04_scripts/" 2>/dev/null || true
cp /home/raspberry/connect_wifi.sh "$OUT/04_scripts/" 2>/dev/null || true

sanitize_file() {
  local src="$1"
  local dst="$2"
  if [ -f "$src" ]; then
    sed -E \
      -e 's/("token"[[:space:]]*:[[:space:]]*")[^"]+(")/\1***TOKEN_OCULTO***\2/g' \
      -e 's/(wifi\|)[^|]+(\|[^|]+\|)[^[:space:]]+/\1***TOKEN_OCULTO***\2***PASSWORD_OCULTO***/g' \
      "$src" > "$dst"
  fi
}

sanitize_file /home/raspberry/web_config.json "$OUT/05_config_sanitizada/web_config.json"
sanitize_file /home/raspberry/wifi_command_config.json "$OUT/05_config_sanitizada/wifi_command_config.json"
sanitize_file /home/raspberry/gpio_shutdown_config.json "$OUT/05_config_sanitizada/gpio_shutdown_config.json"
sanitize_file /home/raspberry/lcd_state.json "$OUT/05_config_sanitizada/lcd_state.json"

sudo cp /etc/sudoers.d/display_modes "$OUT/05_config_sanitizada/sudoers_display_modes" 2>/dev/null || true
sudo cp /etc/sudoers.d/display_wifi "$OUT/05_config_sanitizada/sudoers_display_wifi" 2>/dev/null || true
sudo chown -R raspberry:raspberry "$OUT/05_config_sanitizada" 2>/dev/null || true

for svc in bt-agent-auto.service ble-server.service web-display.service gpio-shutdown.service; do
  journalctl -u "$svc" -n 250 --no-pager 2>/dev/null \
    | sed -E \
      -e 's/(wifi\|)[^|]+(\|[^|]+\|)[^[:space:]]+/\1***TOKEN_OCULTO***\2***PASSWORD_OCULTO***/g' \
      -e 's/(COMMAND=\/home\/raspberry\/connect_wifi\.sh).*/\1 ***ARGUMENTOS_OCULTOS***/g' \
      > "$OUT/06_logs/$svc.log" || true
done

{
  echo "RED"
  hostname -I || true
  nmcli dev status 2>/dev/null || true
  nmcli -t -f NAME,DEVICE,TYPE connection show --active 2>/dev/null || true
  echo ""
  echo "BLUETOOTH"
  bluetoothctl show 2>/dev/null || true
  echo ""
  echo "I2C"
  i2cdetect -y 1 2>/dev/null || true
  echo ""
  echo "GPIO"
  echo "Pin físico 39 = GND"
  echo "Pin físico 40 = GPIO21 / BCM21"
  echo "Puente puesto = normal"
  echo "Puente quitado = cuenta regresiva de apagado"
  echo ""
  echo "DEPENDENCIAS"
  python3 --version
  python3 - <<'PY'
mods = ["bluezero", "RPLCD", "smbus2", "requests", "gpiozero"]
for m in mods:
    try:
        __import__(m)
        print(f"{m}: OK")
    except Exception as e:
        print(f"{m}: ERROR -> {e}")
PY
} > "$OUT/07_red_gpio_lcd.txt"

tar -czf "/home/raspberry/diagnostico_display_$TS.tar.gz" -C /home/raspberry "$(basename "$OUT")"

echo "Diagnóstico creado:"
echo "/home/raspberry/diagnostico_display_$TS.tar.gz"
