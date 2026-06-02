# -*- coding: utf-8 -*-
"""
Modo web + pantalla LCD para Raspberry Pi.

Este archivo reemplaza la entrada BLE por una consulta periódica a una API web.
La página guarda mensajes en el hosting y la Raspberry consulta el endpoint
poll.php cada pocos segundos. Si hay un mensaje nuevo, se muestra en la LCD.

Este modo debe ejecutarse solo, sin el servicio BLE activo, porque ambos modos
controlan la misma pantalla.
"""

from RPLCD.i2c import CharLCD
import threading
import requests
import time
import json
import re
import subprocess
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

CONFIG_PATH = Path("/home/raspberry/web_config.json")

DEFAULT_CONFIG = {
    "poll_url": "https://agas.com.co/api/poll.php",
    "token": "CAMBIA_ESTE_TOKEN",
    "poll_interval": 3,
    "last_id_file": "/home/raspberry/last_web_id.txt",
    "lcd_addr": "0x27",
    "lcd_cols": 16,
    "lcd_rows": 2
}


def load_config():
    """Carga la configuración desde JSON.

    El token y la URL no se dejan quemados en el código para poder cambiarlos
    sin editar el programa.
    """
    if not CONFIG_PATH.exists():
        print("No existe web_config.json. Usando configuración por defecto.", flush=True)
        return DEFAULT_CONFIG.copy()

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    final = DEFAULT_CONFIG.copy()
    final.update(cfg)
    return final


config = load_config()

POLL_URL = config["poll_url"]
TOKEN = config["token"]
POLL_INTERVAL = float(config["poll_interval"])
MAX_CONSECUTIVE_ERRORS = int(config.get("max_consecutive_errors", 5))
LAST_ID_FILE = Path(config["last_id_file"])
LCD_ADDR = int(str(config["lcd_addr"]), 16) if isinstance(config["lcd_addr"], str) else int(config["lcd_addr"])
LCD_COLS = int(config["lcd_cols"])
LCD_ROWS = int(config["lcd_rows"])

SCROLL_DELAY = 0.35
SCROLL_GAP = "   "

# ============================================================
# ESTADO COMPARTIDO DE PANTALLA
# ============================================================

lcd = None
lcd_ok = False

messages = ["Modo web", "iniciando"]
history = ["", ""]
has_history = False
offsets = [0, 0]
lock = threading.Lock()
running = True

DISPLAY_STATE_FILE = Path("/home/raspberry/lcd_state.json")
LCD_OVERRIDE_FILE = Path("/home/raspberry/lcd_override.lock")


def publish_display_state():
    """Guarda el último contenido lógico de la LCD para restaurarlo si hay interrupción GPIO."""
    try:
        data = {
            "line_1": messages[0],
            "line_2": messages[1],
            "ts": time.time()
        }
        DISPLAY_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print("ERROR guardando estado LCD:", e, flush=True)


def display_override_active():
    """Indica si otro servicio, como GPIO shutdown, está tomando control temporal de la LCD."""
    return LCD_OVERRIDE_FILE.exists()



# ============================================================
# LCD
# ============================================================

def init_lcd():
    """Inicializa la pantalla LCD por I2C."""
    global lcd, lcd_ok

    try:
        lcd = CharLCD('PCF8574', LCD_ADDR, cols=LCD_COLS, rows=LCD_ROWS)
        lcd.clear()
        lcd_ok = True
        print("LCD lista en direccion 0x{:02X}".format(LCD_ADDR), flush=True)
    except Exception as e:
        lcd_ok = False
        print("ERROR iniciando LCD:", e, flush=True)


def clean_text(text):
    """Limpia texto recibido desde la web antes de enviarlo a la LCD."""
    text = str(text)
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def line_window(text, offset):
    """Devuelve una ventana de 16 caracteres para mostrar o desplazar texto."""
    text = clean_text(text)

    if not text:
        return " " * LCD_COLS

    if len(text) <= LCD_COLS:
        return text.ljust(LCD_COLS)

    loop_text = text + SCROLL_GAP
    start = offset % len(loop_text)
    visible = (loop_text + loop_text)[start:start + LCD_COLS]
    return visible.ljust(LCD_COLS)


def lcd_loop():
    """Actualiza la LCD en un hilo separado."""
    global offsets

    last_line_1 = None
    last_line_2 = None

    while running:
        with lock:
            line_1 = line_window(messages[0], offsets[0])
            line_2 = line_window(messages[1], offsets[1])

            offsets[0] = offsets[0] + 1 if len(clean_text(messages[0])) > LCD_COLS else 0
            offsets[1] = offsets[1] + 1 if len(clean_text(messages[1])) > LCD_COLS else 0

        if display_override_active():
            last_line_1 = None
            last_line_2 = None
            time.sleep(SCROLL_DELAY)
            continue

        if lcd_ok:
            try:
                if line_1 != last_line_1:
                    lcd.cursor_pos = (0, 0)
                    lcd.write_string(line_1)
                    last_line_1 = line_1

                if line_2 != last_line_2:
                    lcd.cursor_pos = (1, 0)
                    lcd.write_string(line_2)
                    last_line_2 = line_2

            except Exception as e:
                print("ERROR actualizando LCD:", e, flush=True)

        time.sleep(SCROLL_DELAY)


def set_display_lines(line_1, line_2):
    """Cambia directamente las dos líneas visibles."""
    global messages, offsets

    with lock:
        messages = [clean_text(line_1), clean_text(line_2)]
        offsets = [0, 0]
        publish_display_state()


def add_message(text):
    """Agrega un mensaje al historial visible de la LCD."""
    global messages, history, offsets, has_history

    text = clean_text(text)

    if not text:
        return

    with lock:
        previous_last = history[1] if has_history else ""
        history = [previous_last, text]
        messages = history[:]
        offsets = [0, 0]
        has_history = True
        publish_display_state()

    print("Mensaje mostrado. Penultimo='{}' Ultimo='{}'".format(previous_last, text), flush=True)



def request_mode_switch(target_mode):
    """Solicita a systemd cambiar de modo sin bloquear el servicio actual."""
    try:
        print("Solicitando cambio a modo {}...".format(target_mode), flush=True)
        subprocess.Popen([
            "sudo",
            "/usr/bin/systemctl",
            "start",
            "display-mode-switch@{}.service".format(target_mode)
        ])
    except Exception as e:
        print("ERROR solicitando cambio de modo:", e, flush=True)


def is_switch_command(text):
    """Detecta comandos internos enviados desde la página web."""
    command = clean_text(text).lower()
    if command in ("ble", "bluetooth"):
        return "ble"
    return None


# ============================================================
# POLLING WEB
# ============================================================

def read_last_id():
    """Lee el último ID mostrado para no repetir mensajes."""
    try:
        if LAST_ID_FILE.exists():
            return int(LAST_ID_FILE.read_text(encoding="utf-8").strip())
    except Exception as e:
        print("No se pudo leer last_id:", e, flush=True)

    return 0


def save_last_id(last_id):
    """Guarda el último ID mostrado."""
    try:
        LAST_ID_FILE.write_text(str(int(last_id)), encoding="utf-8")
    except Exception as e:
        print("No se pudo guardar last_id:", e, flush=True)


def poll_once(last_id):
    """Consulta la API y devuelve la respuesta JSON."""
    params = {
        "token": TOKEN,
        "last_id": last_id
    }

    response = requests.get(POLL_URL, params=params, timeout=8)
    response.raise_for_status()
    return response.json()


def polling_loop():
    """Consulta la API periódicamente y actualiza la LCD cuando hay mensajes."""
    last_id = read_last_id()
    consecutive_errors = 0

    print("Iniciando polling web desde last_id={}".format(last_id), flush=True)
    set_display_lines("Web lista", "esperando msg")

    while True:
        try:
            data = poll_once(last_id)
            consecutive_errors = 0

            if not data.get("ok"):
                print("Respuesta no OK:", data, flush=True)
                time.sleep(POLL_INTERVAL)
                continue

            message = data.get("message")

            if message:
                msg_id = int(message["id"])
                text = message["mensaje"]

                target_mode = is_switch_command(text)

                if target_mode:
                    add_message("Cambiando a BLE")
                    last_id = msg_id
                    save_last_id(last_id)
                    request_mode_switch(target_mode)
                    return

                add_message(text)
                last_id = msg_id
                save_last_id(last_id)

            time.sleep(POLL_INTERVAL)

        except requests.exceptions.RequestException as e:
            consecutive_errors += 1
            print("ERROR consultando API ({}/{}): {}".format(consecutive_errors, MAX_CONSECUTIVE_ERRORS, e), flush=True)
            set_display_lines("Sin internet", "modo BLE?")

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                add_message("Sin internet")
                add_message("Cambiando BLE")
                request_mode_switch("ble")
                return

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            consecutive_errors += 1
            print("ERROR en polling ({}/{}): {}".format(consecutive_errors, MAX_CONSECUTIVE_ERRORS, e), flush=True)

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                add_message("Error web")
                add_message("Cambiando BLE")
                request_mode_switch("ble")
                return

            time.sleep(POLL_INTERVAL)


def main():
    """Inicializa LCD, levanta el hilo de pantalla y empieza polling web."""
    init_lcd()

    hilo_lcd = threading.Thread(target=lcd_loop, daemon=True)
    hilo_lcd.start()

    polling_loop()


if __name__ == "__main__":
    main()
