# -*- coding: utf-8 -*-
"""
Servidor BLE UART con salida en pantalla LCD 16x2 para Raspberry Pi.

Este archivo corresponde al programa principal del miniproyecto:
la Raspberry Pi se anuncia como un dispositivo Bluetooth Low Energy (BLE),
recibe texto desde un celular mediante un servicio UART y usa una pantalla LCD
I2C como actuador/salida visual.

Nivel del proyecto:
- Miniproyecto de sistemas embebidos.
- Comunicación inalámbrica mediante BLE.
- Actuador/salida: pantalla LCD 16x2 con interfaz I2C.
- Ejecución autónoma como servicio de Linux mediante systemd.
"""

from bluezero import adapter, peripheral, device
from RPLCD.i2c import CharLCD
import threading
import time
import re

# ============================================================
# CONFIGURACIÓN GENERAL DEL SERVICIO BLE UART
# ============================================================
# Se usa un servicio UART BLE compatible con el patrón Nordic UART Service.
# En este esquema hay un servicio principal y dos características:
# - RX: característica donde el celular escribe datos hacia la Raspberry.
# - TX: característica desde donde la Raspberry puede notificar/responder.

UART_SERVICE = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
RX_CHAR      = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'  # Entrada: el celular escribe aquí.
TX_CHAR      = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'  # Salida: la Raspberry responde aquí.

# ============================================================
# CONFIGURACIÓN DE LA PANTALLA LCD
# ============================================================
# La pantalla usada es una LCD 16x2 controlada por I2C mediante un expansor
# PCF8574. La dirección 0x27 es frecuente en módulos LCD I2C comerciales.

LCD_ADDR = 0x27
LCD_COLS = 16
LCD_ROWS = 2

# Velocidad del desplazamiento horizontal para mensajes más largos que 16 caracteres.
SCROLL_DELAY = 0.35

# Separación visual entre el final y el reinicio de un mensaje largo.
SCROLL_GAP = "   "

# ============================================================
# ESTADO GLOBAL COMPARTIDO
# ============================================================
# Estas variables son compartidas por dos partes del programa:
# 1. El hilo que actualiza la LCD constantemente.
# 2. Los callbacks BLE que se ejecutan cuando hay conexión, desconexión o mensajes.

lcd = None
lcd_ok = False

# Texto que la LCD debe mostrar en este momento.
# Inicialmente se usa un mensaje de preparación mientras el sistema arranca.
messages = ["Preparando", "comunicacion"]

# Historial visible de eventos/mensajes importantes.
# Se conservan dos líneas: penúltimo y último mensaje.
history = ["", ""]
has_history = False

# Posición de desplazamiento para cada línea de la LCD.
# offsets[0] controla la línea superior y offsets[1] la línea inferior.
offsets = [0, 0]

# Candado para proteger el acceso a variables compartidas.
# Evita que el hilo de la LCD lea datos mientras un callback BLE los está modificando.
lock = threading.Lock()

# Bandera de control del bucle de la LCD.
running = True


# ============================================================
# FUNCIONES DE MANEJO DE LCD
# ============================================================

def init_lcd():
    """Inicializa la pantalla LCD I2C.

    Si la LCD no responde, el programa no se detiene completamente: se marca
    lcd_ok como False y el servidor BLE puede seguir funcionando. Esto facilita
    el diagnóstico del sistema cuando el problema está solo en la pantalla.
    """
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
    """Normaliza el texto antes de enviarlo a la LCD.

    BLE puede entregar saltos de línea, caracteres invisibles o espacios
    repetidos. La LCD 16x2 no maneja bien esos caracteres, por eso se limpian
    antes de mostrarlos.
    """
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def line_window(text, offset):
    """Devuelve una ventana de 16 caracteres para una línea de LCD.

    Si el texto cabe en la pantalla, se rellena con espacios para limpiar
    caracteres sobrantes de mensajes anteriores. Si el texto es largo, se toma
    una ventana desplazada para generar el efecto de scroll horizontal.
    """
    text = clean_text(text)

    if not text:
        return " " * LCD_COLS

    if len(text) <= LCD_COLS:
        return text.ljust(LCD_COLS)

    loop_text = text + SCROLL_GAP
    start = offset % len(loop_text)

    # Se duplica loop_text para permitir que la ventana continúe desde el inicio
    # cuando el scroll llega al final de la cadena.
    visible = (loop_text + loop_text)[start:start + LCD_COLS]
    return visible.ljust(LCD_COLS)


def lcd_loop():
    """Actualiza la LCD de forma periódica.

    Esta función corre en un hilo independiente para que el desplazamiento del
    texto no bloquee la comunicación BLE. Primero calcula qué líneas deben
    mostrarse y luego escribe en la pantalla solo si hay cambios.
    """
    global offsets

    last_line_1 = None
    last_line_2 = None

    while running:
        # Lectura protegida del estado compartido.
        # Dentro del candado solo se calcula el contenido visible; la escritura
        # física a la LCD se hace después para no retener el lock más tiempo del necesario.
        with lock:
            line_1 = line_window(messages[0], offsets[0])
            line_2 = line_window(messages[1], offsets[1])

            if len(clean_text(messages[0])) > LCD_COLS:
                offsets[0] += 1
            else:
                offsets[0] = 0

            if len(clean_text(messages[1])) > LCD_COLS:
                offsets[1] += 1
            else:
                offsets[1] = 0

        if lcd_ok:
            try:
                # Evita reescrituras innecesarias: solo actualiza una línea si cambió.
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
    """Cambia directamente las dos líneas visibles de la LCD.

    Se usa para mensajes de estado del sistema, por ejemplo cuando la
    comunicación y la pantalla ya están listas. No modifica el historial de
    mensajes recibidos.
    """
    global messages, offsets

    with lock:
        messages = [clean_text(line_1), clean_text(line_2)]
        offsets = [0, 0]


def add_message(text):
    """Agrega un mensaje al historial visible de la LCD.

    El diseño del proyecto conserva solamente dos entradas: la anterior y la
    última. Esto permite usar la LCD 16x2 como una salida simple de historial.
    """
    global messages, history, offsets, has_history

    text = clean_text(text)

    if not text:
        print("Mensaje vacio ignorado", flush=True)
        return

    with lock:
        previous_last = history[1] if has_history else ""
        history = [previous_last, text]
        messages = history[:]
        offsets = [0, 0]
        has_history = True

    print("LCD actualizado. Penultimo='{}' Ultimo='{}'".format(previous_last, text), flush=True)


# ============================================================
# CLASE DE CALLBACKS BLE UART
# ============================================================
# Bluezero usa callbacks: funciones que se ejecutan automáticamente cuando
# ocurre un evento BLE. Esta clase agrupa los callbacks de conexión,
# desconexión, escritura RX y notificación TX.

class UARTDevice:
    # Referencia a la característica TX cuando el cliente activa notificaciones.
    # Si tx_obj es None, la Raspberry puede recibir mensajes pero no enviar respuesta.
    tx_obj = None

    @classmethod
    def on_connect(cls, ble_device: device.Device):
        """Callback ejecutado cuando un dispositivo se conecta por BLE."""
        print("Conectado:", ble_device.address, flush=True)
        add_message("Conectado!!!")

    @classmethod
    def on_disconnect(cls, adapter_address, device_address):
        """Callback ejecutado cuando el dispositivo BLE se desconecta."""
        print("Desconectado:", device_address, flush=True)
        add_message("Sin conexion")

    @classmethod
    def uart_notify(cls, notifying, characteristic):
        """Callback asociado a la activación de notificaciones en TX.

        En BLE, el cliente debe habilitar notificaciones para recibir datos
        enviados por la Raspberry. Cuando eso ocurre, se guarda la característica
        TX para usarla posteriormente en uart_write().
        """
        if notifying:
            print("Notificaciones activadas en TX", flush=True)
            cls.tx_obj = characteristic
        else:
            print("Notificaciones desactivadas en TX", flush=True)
            cls.tx_obj = None

    @classmethod
    def uart_write(cls, value, options):
        """Callback ejecutado cuando el celular escribe en la característica RX."""
        print("raw bytes:", value, flush=True)
        print("options:", options, flush=True)

        try:
            text = bytes(value).decode("utf-8", errors="replace")
        except Exception as e:
            text = str(value)
            print("Error decodificando:", e, flush=True)

        text = clean_text(text)
        print(">>> Mensaje recibido:", text, flush=True)

        # El mensaje recibido se envía al historial visible de la LCD.
        add_message(text)

        # Si el cliente activó notificaciones, se envía una respuesta sencilla.
        if cls.tx_obj:
            respuesta = ("Raspberry recibio: " + text).encode("utf-8")
            cls.tx_obj.set_value(list(respuesta))
        else:
            print("El iPhone aun no activo notificaciones en TX", flush=True)


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    """Configura la LCD, levanta el hilo de pantalla y publica el periférico BLE."""
    init_lcd()

    # El hilo de la LCD permite mantener el scroll sin bloquear los eventos BLE.
    hilo_lcd = threading.Thread(target=lcd_loop, daemon=True)
    hilo_lcd.start()

    # Se toma el primer adaptador Bluetooth disponible en la Raspberry.
    dongle = list(adapter.Adapter.available())[0]
    dongle.powered = True

    # La Raspberry se anuncia como un periférico BLE con nombre visible.
    pi = peripheral.Peripheral(dongle.address, local_name='RaspberryBLE')

    # Servicio principal UART BLE.
    pi.add_service(srv_id=1, uuid=UART_SERVICE, primary=True)

    # Característica RX: canal de escritura desde el celular hacia la Raspberry.
    pi.add_characteristic(
        srv_id=1,
        chr_id=1,
        uuid=RX_CHAR,
        value=[],
        notifying=False,
        flags=['write', 'write-without-response'],
        read_callback=None,
        write_callback=UARTDevice.uart_write,
        notify_callback=None
    )

    # Característica TX: canal de notificación desde la Raspberry hacia el celular.
    pi.add_characteristic(
        srv_id=1,
        chr_id=2,
        uuid=TX_CHAR,
        value=[],
        notifying=False,
        flags=['notify'],
        read_callback=None,
        write_callback=None,
        notify_callback=UARTDevice.uart_notify
    )

    # Eventos generales de conexión y desconexión BLE.
    pi.on_connect = UARTDevice.on_connect
    pi.on_disconnect = UARTDevice.on_disconnect

    print("Servidor BLE UART + LCD listo. Esperando conexion del iPhone...", flush=True)
    set_display_lines("Comunic. lista", "LCD lista")

    # Publica el periférico BLE y deja el servidor activo esperando conexiones.
    pi.publish()


if __name__ == '__main__':
    main()
