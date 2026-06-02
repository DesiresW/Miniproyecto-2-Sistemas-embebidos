# -*- coding: utf-8 -*-
"""
Prueba mínima de la pantalla LCD 16x2 I2C.

Este archivo permite verificar el actuador/salida visual del proyecto sin
levantar el servidor BLE. Es útil para comprobar cableado, dirección I2C y
funcionamiento básico de la librería RPLCD.
"""

from RPLCD.i2c import CharLCD
import time

# Dirección I2C del módulo LCD. En este montaje se usó 0x27.
LCD_ADDR = 0x27


def main():
    """Escribe dos líneas de prueba y limpia la pantalla después de 5 segundos."""
    lcd = CharLCD('PCF8574', LCD_ADDR)
    lcd.clear()

    lcd.write_string('Hola Desires')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('LCD funcionando')

    time.sleep(5)
    lcd.clear()


if __name__ == '__main__':
    main()
