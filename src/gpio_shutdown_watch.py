# -*- coding: utf-8 -*-
"""
Apagado seguro por GPIO con lógica normalmente cerrada y cuenta regresiva en LCD.

Conexión física:
- Pin físico 39 = GND
- Pin físico 40 = GPIO21 / BCM21

Lógica:
- Puente puesto entre 39 y 40  -> funcionamiento normal.
- Puente quitado              -> inicia cuenta regresiva.
- Si el puente vuelve antes del final, se restaura la LCD.
- Si la cuenta termina, se muestra APAGANDO !!! y se ejecuta shutdown.
"""

from gpiozero import Button
import sys
from glob import glob

# El servicio corre como root, pero algunas librerías pueden estar instaladas
# en el entorno del usuario raspberry. Se agregan esas rutas antes de importar RPLCD.
for site_path in glob("/home/raspberry/.local/lib/python*/site-packages"):
    if site_path not in sys.path:
        sys.path.append(site_path)

from RPLCD.i2c import CharLCD
import subprocess
import time
import json
from pathlib import Path

CONFIG_PATH = Path("/home/raspberry/gpio_shutdown_config.json")
DISPLAY_STATE_FILE = Path("/home/raspberry/lcd_state.json")
LCD_OVERRIDE_FILE = Path("/home/raspberry/lcd_override.lock")

DEFAULT_CONFIG = {
    "gpio_pin_bcm": 21,
    "countdown_seconds": 5,
    "bounce_time": 0.3,
    "startup_grace_time": 8,
    "lcd_addr": "0x27",
    "lcd_cols": 16,
    "lcd_rows": 2,
    "services_to_stop": [
        "web-display.service",
        "ble-server.service",
        "bt-agent-auto.service"
    ],
    "shutdown_command": ["/usr/sbin/shutdown", "-h", "now"]
}

shutdown_requested = False
lcd = None
lcd_ok = False


def load_config():
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    final = DEFAULT_CONFIG.copy()
    final.update(cfg)
    return final


config = load_config()


def lcd_address():
    value = config["lcd_addr"]
    return int(value, 16) if isinstance(value, str) else int(value)


def init_lcd():
    global lcd, lcd_ok

    try:
        lcd = CharLCD(
            "PCF8574",
            lcd_address(),
            cols=int(config["lcd_cols"]),
            rows=int(config["lcd_rows"])
        )
        lcd_ok = True
    except Exception as e:
        lcd_ok = False
        print("ERROR iniciando LCD desde GPIO:", e, flush=True)


def clean_line(text):
    """Devuelve una línea exactamente del ancho de la LCD."""
    cols = int(config["lcd_cols"])
    text = str(text).replace("\r", " ").replace("\n", " ")
    return text[:cols].ljust(cols)


def write_lcd(line_1, line_2):
    """Escribe dos líneas limpias en la LCD.

    Se usa lcd.clear() antes de escribir para evitar residuos de mensajes
    anteriores durante la rutina de apagado por GPIO.
    """
    if not lcd_ok:
        return

    try:
        lcd.clear()
        time.sleep(0.05)

        lcd.cursor_pos = (0, 0)
        lcd.write_string(clean_line(line_1))

        lcd.cursor_pos = (1, 0)
        lcd.write_string(clean_line(line_2))

    except Exception as e:
        print("ERROR escribiendo LCD desde GPIO:", e, flush=True)


def clear_lcd_before_shutdown():
    """Borra la pantalla justo antes de solicitar el apagado del sistema."""
    if not lcd_ok:
        return

    try:
        lcd.clear()
        print("LCD borrada antes del apagado.", flush=True)
    except Exception as e:
        print("ERROR borrando LCD antes del apagado:", e, flush=True)

def read_previous_display():
    try:
        if DISPLAY_STATE_FILE.exists():
            data = json.loads(DISPLAY_STATE_FILE.read_text(encoding="utf-8"))
            return data.get("line_1", ""), data.get("line_2", "")
    except Exception as e:
        print("ERROR leyendo estado LCD:", e, flush=True)

    return "Pantalla", "en espera"


def restore_display(previous):
    line_1, line_2 = previous
    write_lcd(line_1, line_2)

    try:
        LCD_OVERRIDE_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def run_command(cmd, timeout=15):
    try:
        print("Ejecutando:", " ".join(cmd), flush=True)
        subprocess.run(cmd, check=False, timeout=timeout)
    except Exception as e:
        print("Error ejecutando comando:", cmd, e, flush=True)


def request_shutdown():
    global shutdown_requested

    if shutdown_requested:
        return

    shutdown_requested = True

    write_lcd("APAGANDO !!!", "Espere...")
    print("Cuenta terminada. Iniciando apagado seguro...", flush=True)

    for service in config["services_to_stop"]:
        run_command(["/usr/bin/systemctl", "stop", service])

    # Se deja visible el aviso final unos segundos y luego se limpia la pantalla.
    time.sleep(2)
    clear_lcd_before_shutdown()

    run_command(["/usr/bin/sync"], timeout=5)
    time.sleep(1)
    run_command(config["shutdown_command"], timeout=5)


def countdown_or_cancel(bridge):
    previous_display = read_previous_display()

    try:
        LCD_OVERRIDE_FILE.write_text("gpio-shutdown", encoding="utf-8")
    except Exception:
        pass

    countdown = int(config["countdown_seconds"])

    for remaining in range(countdown, 0, -1):
        if bridge.is_pressed:
            print("Puente reconectado. Cancelando apagado.", flush=True)
            restore_display(previous_display)
            return

        write_lcd("Seguro apagar?", "Cuenta: {}".format(remaining))
        print("Cuenta apagado:", remaining, flush=True)

        for _ in range(10):
            time.sleep(0.1)
            if bridge.is_pressed:
                print("Puente reconectado. Cancelando apagado.", flush=True)
                restore_display(previous_display)
                return

    request_shutdown()


def main():
    pin = int(config["gpio_pin_bcm"])
    bounce_time = float(config["bounce_time"])
    startup_grace_time = float(config["startup_grace_time"])

    print("Servicio GPIO shutdown activo", flush=True)
    print("Usando GPIO BCM{} / pin físico 40".format(pin), flush=True)
    print("Normal: puente cerrado entre pin 39 y 40", flush=True)
    print("Apagado: retirar puente durante {} segundos".format(config["countdown_seconds"]), flush=True)
    print("Gracia inicial: {} segundos".format(startup_grace_time), flush=True)

    init_lcd()

    bridge = Button(pin, pull_up=True, bounce_time=bounce_time)

    time.sleep(startup_grace_time)

    open_event_active = False

    while True:
        if bridge.is_pressed:
            open_event_active = False
        else:
            if not open_event_active:
                open_event_active = True
                print("Puente abierto detectado. Iniciando cuenta regresiva...", flush=True)
                countdown_or_cancel(bridge)

        time.sleep(0.2)


if __name__ == "__main__":
    main()
