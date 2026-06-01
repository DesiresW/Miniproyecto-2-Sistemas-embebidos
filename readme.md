# Miniproyecto 2 - Sistemas Embebidos

## Autores

- Jose Miguel Sánchez Vargas
- Juan Pablo Prieto Vergara
- Vladimir

## Descripción

Este proyecto implementa una comunicación inalámbrica básica entre un celular y una Raspberry Pi usando Bluetooth Low Energy (BLE). Los mensajes enviados desde el cliente BLE son recibidos por la Raspberry y mostrados en una pantalla LCD 16x2 conectada por I2C.

La idea del montaje es sencilla: usar la Raspberry como controlador, BLE como medio de comunicación inalámbrica y la pantalla LCD como salida visual del sistema. El proyecto se desarrolló como ejercicio práctico para integrar software, comunicación y un dispositivo físico de salida en un entorno embebido.

## Objetivo

Recibir mensajes de forma inalámbrica en una Raspberry Pi y mostrarlos en una pantalla LCD 16x2, usando Python, BLE y comunicación I2C.

## Funcionamiento

Al iniciar, la Raspberry configura la pantalla LCD y publica un servicio BLE. Desde un celular o cliente compatible se puede establecer conexión y enviar mensajes de texto.

Cuando llega un mensaje, el programa lo limpia, actualiza el historial interno y lo muestra en la LCD. La pantalla conserva los dos mensajes más recientes. Si el texto supera el ancho de 16 caracteres, se desplaza horizontalmente para facilitar su lectura.

También se muestran eventos básicos del sistema, como conexión y desconexión del cliente BLE:

```text
Conectado!!!
Sin conexion
```

## Estructura del repositorio

```text
.
├── src/
│   ├── ble_server.py
│   └── test_lcd.py
├── systemd/
│   ├── ble-server.service
│   └── bt-agent-auto.service
└── .gitignore
```

## Archivos principales

`src/ble_server.py` contiene el programa principal. Configura el servidor BLE, recibe mensajes, controla el historial y actualiza la pantalla LCD.

`src/test_lcd.py` permite probar la pantalla LCD de forma independiente, antes de ejecutar el sistema completo.

`systemd/ble-server.service` permite ejecutar el programa principal como servicio de Linux.

`systemd/bt-agent-auto.service` inicia un agente Bluetooth automático para facilitar la conexión desde dispositivos externos.

## Requisitos

- Raspberry Pi con Bluetooth disponible.
- Pantalla LCD 16x2 con módulo I2C.
- Python 3.
- Bluetooth habilitado en Raspberry Pi OS.
- Bibliotecas de Python para BLE y LCD.

Dependencias principales:

```bash
sudo apt update
sudo apt install python3-pip bluetooth bluez
pip3 install bluezero RPLCD smbus2
```

En este montaje la pantalla LCD trabajó con dirección I2C `0x27`. Si otra pantalla usa una dirección diferente, debe ajustarse en el código.

## Prueba de la pantalla

Antes de ejecutar el servidor BLE, se puede probar la LCD con:

```bash
python3 src/test_lcd.py
```

Si la conexión I2C está correcta, la pantalla debe mostrar un mensaje de prueba.

## Ejecución manual

Para ejecutar el proyecto desde la terminal:

```bash
python3 src/ble_server.py
```

Mientras el programa esté activo, la Raspberry quedará esperando una conexión BLE y mostrará en la LCD los mensajes recibidos.

## Ejecución como servicio

Para dejar el proyecto funcionando automáticamente al iniciar la Raspberry, se incluyen dos archivos de servicio para `systemd`.

Copiar los servicios:

```bash
sudo cp systemd/bt-agent-auto.service /etc/systemd/system/bt-agent-auto.service
sudo cp systemd/ble-server.service /etc/systemd/system/ble-server.service
```

Recargar `systemd`:

```bash
sudo systemctl daemon-reload
```

Habilitar los servicios:

```bash
sudo systemctl enable bt-agent-auto.service
sudo systemctl enable ble-server.service
```

Iniciarlos:

```bash
sudo systemctl start bt-agent-auto.service
sudo systemctl start ble-server.service
```

Verificar el estado:

```bash
systemctl status ble-server.service --no-pager
```

Ver los registros en tiempo real:

```bash
journalctl -u ble-server.service -f
```

## Notas de implementación

El programa usa un servicio BLE tipo UART. El cliente escribe datos en una característica de recepción y la Raspberry los procesa como texto.

La actualización de la LCD se ejecuta en un hilo separado para no bloquear la comunicación BLE. Para evitar conflictos entre el hilo de pantalla y los eventos de recepción, se usa un bloqueo (`threading.Lock`) sobre las variables compartidas del historial y del texto visible.

Los archivos `.service` permiten que el sistema no dependa de abrir manualmente una terminal. Esto es útil cuando la Raspberry se usa como dispositivo embebido autónomo.

## Estado del proyecto

El proyecto fue probado en Raspberry Pi con una pantalla LCD 16x2 por I2C y ejecución automática mediante `systemd`.

El alcance actual cubre la recepción inalámbrica de mensajes y su visualización en pantalla. No incluye aplicación móvil propia, almacenamiento de mensajes ni autenticación avanzada.

