# Raspberry BLE LCD Message Display

## Autores

* Jose Miguel Sánchez Vargas
* Juan Pablo Prieto Vergara

## Descripción general

Este repositorio presenta un miniproyecto académico de sistemas embebidos desarrollado sobre una Raspberry Pi. El proyecto integra una comunicación inalámbrica mediante Bluetooth Low Energy (BLE) con una salida visual física mediante una pantalla LCD 16x2 conectada por bus I2C.

El objetivo principal es demostrar cómo una Raspberry Pi puede recibir información enviada desde un dispositivo externo, procesarla localmente y mostrarla en un actuador o dispositivo de salida. En este caso, la pantalla LCD funciona como salida visual del sistema, permitiendo observar mensajes recibidos y eventos básicos de conexión.

## Objetivo

Implementar una comunicación inalámbrica entre un dispositivo externo y una Raspberry Pi, utilizando Bluetooth Low Energy, para mostrar mensajes en una pantalla LCD 16x2 conectada por I2C.

## Alcance del proyecto

Este proyecto corresponde a una práctica introductoria de sistemas embebidos. No busca presentar una solución industrial ni un producto IoT terminado, sino evidenciar la integración funcional de:

* Una Raspberry Pi como controlador principal.
* Una pantalla LCD 16x2 como dispositivo de salida.
* Comunicación inalámbrica mediante BLE.
* Un programa en Python encargado de recibir, procesar y mostrar mensajes.
* Servicios `systemd` para ejecutar el sistema automáticamente al iniciar la Raspberry Pi.

## Funcionamiento general

El sistema trabaja de la siguiente manera:

1. La Raspberry Pi inicia el programa principal mediante un servicio de `systemd`.
2. El programa configura la pantalla LCD y el adaptador Bluetooth.
3. La Raspberry Pi se anuncia como un dispositivo BLE.
4. Un celular o cliente BLE se conecta a la Raspberry.
5. El cliente envía un mensaje de texto.
6. La Raspberry recibe el mensaje, lo limpia y lo procesa.
7. El mensaje se muestra en la pantalla LCD 16x2.
8. Los eventos de conexión y desconexión también se muestran como mensajes en la pantalla.

La pantalla conserva un historial básico de dos líneas, correspondiente a los dos mensajes más recientes. Cuando un mensaje supera los 16 caracteres, el programa aplica desplazamiento horizontal para permitir su lectura.

## Arquitectura del sistema

```text
Cliente BLE / Celular
        |
        | Comunicación Bluetooth Low Energy
        v
Raspberry Pi
        |
        | Bus I2C
        v
Pantalla LCD 16x2
```

La Raspberry Pi cumple el rol de controlador embebido. El cliente BLE actúa como fuente externa de datos y la pantalla LCD funciona como salida visual del sistema.

## Componentes utilizados

### Hardware

* Raspberry Pi con Bluetooth integrado o adaptador Bluetooth compatible.
* Pantalla LCD 16x2 con módulo I2C basado en PCF8574.
* Cables de conexión para el bus I2C.
* Fuente de alimentación para la Raspberry Pi.

### Software

* Raspberry Pi OS o sistema Linux compatible.
* Python 3.
* Biblioteca `bluezero` para la comunicación BLE.
* Biblioteca `RPLCD` para el manejo de la pantalla LCD.
* `systemd` para ejecutar el programa como servicio del sistema.

## Estructura del repositorio

```text
raspberry-ble-lcd-message-display/
├── src/
│   ├── ble_server.py
│   └── test_lcd.py
├── systemd/
│   ├── ble-server.service
│   └── bt-agent-auto.service
└── .gitignore
```

## Descripción de archivos

### `src/ble_server.py`

Archivo principal del proyecto. Configura la Raspberry Pi como servidor BLE, recibe mensajes enviados desde un cliente externo, administra el historial de mensajes y actualiza la pantalla LCD.

Entre sus funciones principales se encuentran:

* Inicializar la pantalla LCD por I2C.
* Crear un servidor BLE tipo UART.
* Recibir mensajes escritos por un cliente BLE.
* Mostrar los mensajes en una pantalla LCD 16x2.
* Registrar eventos de conexión y desconexión.
* Aplicar desplazamiento horizontal cuando el texto supera el ancho de la pantalla.

### `src/test_lcd.py`

Archivo de prueba para verificar el funcionamiento de la pantalla LCD sin ejecutar el servidor BLE completo. Permite comprobar que la dirección I2C y la conexión física de la pantalla sean correctas.

### `systemd/ble-server.service`

Servicio principal de `systemd`. Ejecuta automáticamente el programa `ble_server.py`, define el usuario de ejecución, el directorio de trabajo, las dependencias y el comportamiento de reinicio del sistema.

### `systemd/bt-agent-auto.service`

Servicio auxiliar para iniciar un agente Bluetooth automático. Su función es facilitar la autorización de conexiones Bluetooth en un entorno sin interfaz gráfica permanente.

## Lógica del programa principal

El archivo `ble_server.py` se organiza alrededor de cuatro bloques funcionales:

### 1. Configuración del sistema

Se definen los identificadores del servicio BLE, las características de recepción y transmisión, la dirección I2C de la pantalla LCD y los parámetros de visualización.

La pantalla utilizada se configura con dirección I2C:

```python
LCD_ADDR = 0x27
```

Y con tamaño:

```python
LCD_COLS = 16
LCD_ROWS = 2
```

### 2. Control de la pantalla LCD

El programa inicializa la pantalla LCD y mantiene un ciclo de actualización independiente. Esta actualización se ejecuta en un hilo separado para que la visualización no bloquee la recepción de mensajes por BLE.

Cuando el texto cabe en la pantalla, se muestra directamente. Cuando el texto es más largo que 16 caracteres, el programa crea una ventana móvil para producir un desplazamiento horizontal.

### 3. Manejo de mensajes

Cada mensaje recibido se limpia antes de mostrarse. El programa elimina saltos de línea, caracteres de control y espacios repetidos para evitar errores visuales en la pantalla.

El sistema mantiene dos mensajes visibles:

```text
Mensaje anterior
Mensaje más reciente
```

Los eventos de conexión y desconexión también se agregan al historial con mensajes simples:

```text
Conectado!!!
Sin conexion
```

### 4. Comunicación BLE

La Raspberry Pi se configura como periférico BLE. El cliente externo puede conectarse y escribir datos en una característica de recepción. El programa recibe esos datos como bytes, los convierte a texto y los muestra en la pantalla LCD.

El flujo básico es:

```text
Cliente BLE envía mensaje
        ↓
Raspberry recibe bytes
        ↓
Python convierte bytes a texto
        ↓
El texto se limpia
        ↓
El mensaje se muestra en la LCD
```

## Instalación básica

Instalar las dependencias necesarias:

```bash
sudo apt update
sudo apt install python3-pip bluetooth bluez
pip3 install bluezero RPLCD smbus2
```

Verificar que la pantalla LCD esté conectada correctamente al bus I2C. En este proyecto se utilizó la dirección `0x27`.

Ejecutar la prueba de pantalla:

```bash
python3 src/test_lcd.py
```

Si la pantalla responde correctamente, se puede ejecutar el servidor BLE:

```bash
python3 src/ble_server.py
```

## Instalación como servicio

Para que el sistema se ejecute automáticamente al iniciar la Raspberry Pi, se pueden copiar los archivos `.service` a la carpeta de servicios de Linux:

```bash
sudo cp systemd/bt-agent-auto.service /etc/systemd/system/bt-agent-auto.service
sudo cp systemd/ble-server.service /etc/systemd/system/ble-server.service
```

Recargar `systemd`:

```bash
sudo systemctl daemon-reload
```

Habilitar los servicios para que inicien automáticamente:

```bash
sudo systemctl enable bt-agent-auto.service
sudo systemctl enable ble-server.service
```

Iniciar los servicios:

```bash
sudo systemctl start bt-agent-auto.service
sudo systemctl start ble-server.service
```

Verificar el estado del servicio principal:

```bash
systemctl status ble-server.service --no-pager
```

Consultar los logs en vivo:

```bash
journalctl -u ble-server.service -f
```

## Consideraciones importantes

Antes de replicar el proyecto, se debe tener en cuenta:

* La dirección I2C de la pantalla puede cambiar según el módulo utilizado.
* El archivo `ble-server.service` debe apuntar a la ruta real donde se encuentre `ble_server.py`.
* El servicio Bluetooth del sistema debe estar activo.
* El cliente BLE debe ser compatible con escritura sobre características BLE.
* Si se cambia el nombre del archivo principal o su ubicación, también debe actualizarse la línea `ExecStart` del servicio.

## Limitaciones

Este proyecto tiene un alcance académico e introductorio. Algunas limitaciones son:

* No incluye aplicación móvil propia.
* No implementa autenticación avanzada.
* No almacena mensajes en una base de datos.
* No tiene interfaz gráfica.
* No está diseñado como solución comercial.
* La pantalla LCD se usa como salida visual básica, no como interfaz completa de usuario.

## Posibles mejoras

Algunas mejoras futuras podrían ser:

* Agregar botones físicos para navegar entre mensajes.
* Incorporar otros actuadores como LED, buzzer o relé.
* Diseñar una aplicación móvil sencilla para enviar mensajes BLE.
* Guardar mensajes en un archivo local.
* Agregar configuración externa para modificar nombre BLE, dirección LCD o velocidad de desplazamiento.
* Documentar el montaje físico con fotografías o diagrama de conexión.

## Estado del proyecto

El sistema fue probado en Raspberry Pi con ejecución automática mediante `systemd`. La versión actual conserva el archivo principal del servidor BLE, un archivo de prueba para la pantalla LCD y los servicios necesarios para el arranque automático.

## Descripción corta para GitHub

Miniproyecto de sistemas embebidos: comunicación inalámbrica BLE con Raspberry Pi y salida visual en LCD 16x2.

## Licencia

Proyecto académico. Definir licencia antes de su publicación final si se desea permitir reutilización formal del código.
