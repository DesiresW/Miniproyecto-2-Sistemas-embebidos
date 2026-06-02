#!/usr/bin/env bash
# organize_legacy.sh
# Mueve versiones viejas conocidas a una carpeta legacy sin borrar nada.

set -euo pipefail

LEGACY_DIR="/home/raspberry/legacy_display_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LEGACY_DIR"

move_if_exists() {
  local item="$1"
  if [ -e "$item" ]; then
    mv "$item" "$LEGACY_DIR/"
    echo "Movido: $item -> $LEGACY_DIR/"
  fi
}

# Versiones históricas del proyecto BLE.
for f in \
  /home/raspberry/backup.py \
  /home/raspberry/ble_server_backup.py \
  /home/raspberry/ble_server_backup_lcd.py \
  /home/raspberry/ble_server_lcd.py \
  /home/raspberry/ble_server_lcd_final.py \
  /home/raspberry/ble_server_lcd_sin_recibido.py \
  /home/raspberry/ble_server_lcd_historial_limpio.py \
  /home/raspberry/ble_server_lcd_carrusel_directo.py \
  /home/raspberry/punto.py \
  /home/raspberry/punto2.py \
  /home/raspberry/prueba.py
do
  move_if_exists "$f"
done

echo ""
echo "Limpieza terminada. Carpeta legacy:"
echo "$LEGACY_DIR"
