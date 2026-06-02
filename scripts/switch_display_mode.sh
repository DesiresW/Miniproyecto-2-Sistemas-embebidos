#!/usr/bin/env bash
# switch_display_mode.sh
# Cambia entre modo BLE y modo Web con un solo comando.
# El servicio de apagado por GPIO no se toca: debe permanecer activo en ambos modos.

set -euo pipefail

BLE_SERVICE="ble-server.service"
BT_AGENT_SERVICE="bt-agent-auto.service"
WEB_SERVICE="web-display.service"
GPIO_SERVICE="gpio-shutdown.service"

require_root() {
  if [ "${EUID}" -ne 0 ]; then
    echo "Ejecuta con sudo:"
    echo "  sudo ./switch_display_mode.sh ble"
    echo "  sudo ./switch_display_mode.sh web"
    exit 1
  fi
}

exists_service() {
  systemctl cat "$1" >/dev/null 2>&1
}

stop_disable() {
  local svc="$1"
  if exists_service "$svc"; then
    systemctl stop "$svc" >/dev/null 2>&1 || true
    systemctl disable "$svc" >/dev/null 2>&1 || true
    systemctl reset-failed "$svc" >/dev/null 2>&1 || true
  fi
}

enable_start() {
  local svc="$1"
  if ! exists_service "$svc"; then
    echo "ERROR: no existe el servicio $svc"
    echo "Instala primero los archivos .service y ejecuta:"
    echo "  sudo systemctl daemon-reload"
    exit 1
  fi

  systemctl enable "$svc" >/dev/null
  systemctl start "$svc"
}

show_status() {
  echo ""
  echo "Estado actual:"
  for svc in "$BT_AGENT_SERVICE" "$BLE_SERVICE" "$WEB_SERVICE" "$GPIO_SERVICE"; do
    if exists_service "$svc"; then
      printf "  %-24s %s\n" "$svc" "$(systemctl is-active "$svc" 2>/dev/null || true)"
    else
      printf "  %-24s %s\n" "$svc" "no instalado"
    fi
  done
}

case "${1:-}" in
  ble)
    require_root
    echo "Cambiando a modo BLE..."
    stop_disable "$WEB_SERVICE"
    enable_start "$BT_AGENT_SERVICE"
    enable_start "$BLE_SERVICE"
    enable_start "$GPIO_SERVICE"
    show_status
    ;;

  web)
    require_root
    echo "Cambiando a modo WEB..."
    stop_disable "$BLE_SERVICE"
    stop_disable "$BT_AGENT_SERVICE"
    enable_start "$WEB_SERVICE"
    enable_start "$GPIO_SERVICE"
    show_status
    ;;

  stop)
    require_root
    echo "Deteniendo modos de pantalla..."
    stop_disable "$BLE_SERVICE"
    stop_disable "$BT_AGENT_SERVICE"
    stop_disable "$WEB_SERVICE"
    enable_start "$GPIO_SERVICE"
    show_status
    ;;

  status)
    show_status
    ;;

  *)
    echo "Uso:"
    echo "  sudo ./switch_display_mode.sh ble      # activa BLE + bt-agent"
    echo "  sudo ./switch_display_mode.sh web      # activa polling web"
    echo "  sudo ./switch_display_mode.sh stop     # detiene BLE y Web"
    echo "  ./switch_display_mode.sh status        # muestra estado"
    exit 1
    ;;
esac
