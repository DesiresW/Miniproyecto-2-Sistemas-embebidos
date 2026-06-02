# Miniproyecto 2 - Sistemas Embebidos

## Autores

* Jose Miguel Sánchez Vargas
* Juan Pablo Prieto Vergara
* Vladimir Enrique Alvarez

## Descripción

Este proyecto implementa un sistema embebido de visualización de mensajes en una pantalla LCD 16x2 conectada a una Raspberry Pi por comunicación I2C. El sistema permite recibir mensajes por dos medios inalámbricos: Bluetooth Low Energy (BLE) y una página web pública conectada a una API alojada en un hosting.

La Raspberry Pi actúa como controlador principal. En modo BLE, recibe mensajes directamente desde un cliente Bluetooth compatible. En modo Web, consulta periódicamente una API en internet, obtiene los mensajes enviados desde la página web y los muestra en la pantalla LCD. Además, el sistema incluye cambio automático entre modos, reconexión WiFi mediante comandos BLE, recuperación ante fallos de internet y apagado seguro mediante un puente físico conectado a GPIO.

La propuesta parte de un ejercicio básico de comunicación inalámbrica y salida física, pero se amplió hasta integrar servicios de Linux, control de red, comunicación web, comandos internos y una rutina de apagado segura.

## Objetivo

Implementar un sistema embebido en Raspberry Pi capaz de recibir mensajes de forma inalámbrica, mostrarlos en una pantalla LCD 16x2 y administrar distintos modos de operación mediante servicios de Linux, comandos remotos y una entrada física por GPIO.

## Funcionamiento general

El sistema tiene dos modos principales de operación:

```text
Modo BLE:
Cliente BLE → Raspberry Pi → LCD 16x2

Modo Web:
Página web → API PHP/MySQL → Raspberry Pi → LCD 16x2
```

En modo BLE, la Raspberry publica un servicio Bluetooth Low Energy tipo UART. Un cliente BLE puede conectarse al dispositivo, escribir mensajes y enviarlos a una característica de recepción. El programa en Python recibe esos datos, los convierte en texto, los limpia y los envía al historial visible de la LCD.

En modo Web, la página pública permite enviar mensajes desde un navegador. El mensaje se guarda en una base de datos mediante una API PHP. La Raspberry consulta periódicamente un endpoint de la API usando polling. Cuando detecta un mensaje nuevo, lo muestra en la LCD.

La pantalla conserva los dos mensajes más recientes. Cuando un mensaje supera el ancho de 16 caracteres, el texto se desplaza horizontalmente para facilitar su lectura.

Además, el sistema reconoce comandos internos. Desde BLE se puede cambiar al modo Web o enviar credenciales WiFi para conectar la Raspberry a una red. Desde la página web se puede enviar un comando para volver al modo BLE. Si el modo Web no puede consultar la API después de varios intentos, la Raspberry cambia automáticamente a modo BLE para facilitar la recuperación de la conexión.

## Estructura del repositorio

```text
.
├── config/
│   ├── gpio_shutdown_config.example.json
│   ├── web_config.example.json
│   └── wifi_command_config.example.json
├── docs/
│   └── comandos_actualizar_repo.md
├── scripts/
│   ├── connect_wifi.sh
│   ├── install_display_project.sh
│   ├── organize_legacy.sh
│   └── switch_display_mode.sh
├── src/
│   ├── ble_server.py
│   ├── gpio_shutdown_watch.py
│   ├── test_lcd.py
│   └── web_poll_display.py
├── systemd/
│   ├── ble-server.service
│   ├── bt-agent-auto.service
│   ├── display-mode-switch@.service
│   ├── gpio-shutdown.service
│   └── web-display.service
├── tools/
│   └── windows/
│       └── send_ble.py
├── web_api/
│   ├── config.example.php
│   ├── poll.php
│   ├── send_message.php
│   └── status.php
├── wordpress/
│   └── bloque_formulario.html
├── .gitignore
├── README.md
└── requirements.txt
```

## Archivos principales

`src/ble_server.py` contiene el modo BLE. Publica el servicio Bluetooth, recibe mensajes, interpreta comandos especiales, actualiza el historial y controla la pantalla LCD.

`src/web_poll_display.py` contiene el modo Web. Consulta periódicamente la API, muestra mensajes nuevos en la LCD y cambia automáticamente a BLE si falla la conexión con el servidor.

`src/gpio_shutdown_watch.py` contiene la rutina de apagado físico. Escucha el estado de un puente entre los pines físicos 39 y 40. Si el puente se retira, muestra una cuenta regresiva en la LCD y ejecuta un apagado seguro si no se reconecta a tiempo.

`src/test_lcd.py` permite probar la pantalla LCD de forma independiente.

`scripts/switch_display_mode.sh` permite cambiar entre modo BLE y modo Web con un solo comando.

`scripts/connect_wifi.sh` permite conectar la Raspberry a una red WiFi usando `nmcli`. Es usado internamente cuando se recibe un comando BLE con credenciales de red.

`systemd/ble-server.service` ejecuta el modo BLE como servicio de Linux.

`systemd/bt-agent-auto.service` levanta un agente Bluetooth automático necesario para facilitar la conexión BLE.

`systemd/web-display.service` ejecuta el modo Web como servicio de Linux.

`systemd/gpio-shutdown.service` mantiene activa la rutina de apagado por GPIO.

`systemd/display-mode-switch@.service` permite lanzar cambios de modo desde otros servicios sin bloquear el proceso actual.

`web_api/` contiene los endpoints PHP para guardar mensajes, consultar el estado de la Raspberry y entregar mensajes nuevos.

`wordpress/bloque_formulario.html` contiene el bloque HTML, CSS y JavaScript usado para insertar el formulario en una página de WordPress.

`tools/windows/send_ble.py` permite enviar mensajes BLE desde un computador Windows usando Python y `bleak`.

## Hardware utilizado

* Raspberry Pi con Bluetooth y WiFi.
* Pantalla LCD 16x2.
* Módulo I2C para LCD basado en PCF8574.
* Conexión I2C de la LCD en dirección `0x27`.
* Puente hembra-hembra de 2.54 mm para la entrada física de apagado.
* Conexión GPIO para apagado:

  * Pin físico 39: GND.
  * Pin físico 40: GPIO21 / BCM21.

La lógica del puente físico es normalmente cerrada:

```text
Puente puesto entre pin 39 y 40  → funcionamiento normal
Puente retirado                  → inicia cuenta regresiva de apagado
```

## Requisitos de software

El proyecto usa dependencias del sistema operativo, bibliotecas de Python, herramientas de red, servicios de Linux y componentes web.

### Software base esperado en Raspberry Pi OS

Normalmente ya viene instalado o disponible en Raspberry Pi OS:

* `systemd`: administra los servicios del proyecto.
* `journalctl`: permite revisar logs de los servicios.
* `ssh`: permite administrar la Raspberry de forma remota.
* `sudo`: permite ejecutar acciones administrativas.
* `python3`: ejecuta los programas principales.
* `nmcli` / NetworkManager: administra conexiones WiFi.
* `bluetoothd`: servicio base de Bluetooth en Linux.

### Dependencias del sistema a instalar

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv bluetooth bluez bluez-tools i2c-tools network-manager python3-requests python3-gpiozero python3-lgpio
```

Descripción general:

* `python3`: intérprete usado para ejecutar los scripts.
* `python3-pip`: permite instalar bibliotecas de Python cuando sea necesario.
* `python3-venv`: permite crear entornos virtuales de Python.
* `bluetooth` y `bluez`: habilitan la pila Bluetooth/BLE de Linux.
* `bluez-tools`: aporta herramientas como `bt-agent`.
* `i2c-tools`: permite diagnosticar dispositivos I2C con comandos como `i2cdetect`.
* `network-manager`: permite administrar redes con `nmcli`.
* `python3-requests`: permite consultar la API web desde Python.
* `python3-gpiozero`: permite leer el estado del GPIO.
* `python3-lgpio`: backend recomendado para GPIO en versiones recientes de Raspberry Pi OS.

### Dependencias de Python

Las bibliotecas usadas por el proyecto son:

```bash
pip3 install bluezero RPLCD smbus2 bleak
```

En Raspberry Pi OS puede ser necesario usar un entorno virtual o instalar algunas dependencias mediante paquetes del sistema, según la configuración del sistema.

Descripción:

* `bluezero`: permite crear el periférico BLE y publicar el servicio UART.
* `RPLCD`: permite controlar la pantalla LCD 16x2.
* `smbus2`: permite comunicación I2C desde Python.
* `requests`: permite hacer consultas HTTP a la API web.
* `gpiozero`: permite leer el estado del pin GPIO de apagado.
* `bleak`: se usa en Windows para enviar mensajes BLE desde computador.

También se usan módulos estándar de Python que no requieren instalación adicional:

* `threading`
* `time`
* `re`
* `json`
* `pathlib`
* `subprocess`
* `glob`
* `sys`

### Herramientas adicionales usadas durante el desarrollo

* `ssh`: acceso remoto a la Raspberry.
* `scp`: transferencia de archivos entre Windows y Raspberry.
* `git`: control de versiones.
* `FileZilla Client`: subida de archivos PHP al hosting.
* `phpMyAdmin`: creación y revisión de tablas MySQL.
* `WordPress`: interfaz visual para el formulario público.
* `CMD` / PowerShell en Windows: ejecución de pruebas BLE, Git y transferencia de archivos.
* `netsh wlan`: consulta de perfiles WiFi guardados en Windows.
* `journalctl`: depuración de servicios.
* `nmcli`: diagnóstico y conexión a redes WiFi.
* `i2cdetect`: diagnóstico de la pantalla LCD en el bus I2C.

## Habilitación de I2C

La interfaz I2C debe estar habilitada en la Raspberry Pi. Puede activarse con:

```bash
sudo raspi-config
```

Luego se debe entrar a las opciones de interfaz y activar I2C.

Para verificar que la pantalla aparece en el bus:

```bash
i2cdetect -y 1
```

En este montaje la pantalla LCD respondió en la dirección:

```text
0x27
```

## Base de datos y API web

El modo Web usa una base de datos MySQL/MariaDB y una API PHP. La base de datos mínima contiene dos tablas: una para mensajes y otra para estado de la Raspberry.

### Tablas mínimas

```sql
CREATE TABLE mensajes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  mensaje VARCHAR(160) NOT NULL,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE estado (
  id INT PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL,
  ultimo_aviso TIMESTAMP NULL,
  activo TINYINT(1) DEFAULT 0
);

INSERT INTO estado (id, nombre, activo)
VALUES (1, 'raspberry', 0);
```

### Endpoints usados

```text
send_message.php  → recibe mensajes desde la página web
poll.php          → entrega mensajes nuevos a la Raspberry
status.php        → informa si la Raspberry está activa
config.php        → contiene configuración de conexión a base de datos
```

El archivo `config.php` no debe subirse con contraseñas reales al repositorio. Para eso se usa `config.example.php`.

## Configuración local en la Raspberry

Los archivos reales de configuración se ubican en `/home/raspberry/` y no deben contenerse con valores sensibles dentro del repositorio público.

### Configuración del modo Web

Archivo:

```text
/home/raspberry/web_config.json
```

Ejemplo:

```json
{
  "poll_url": "https://agas.com.co/api/poll.php",
  "token": "CAMBIA_ESTE_TOKEN",
  "poll_interval": 3,
  "last_id_file": "/home/raspberry/last_web_id.txt",
  "lcd_addr": "0x27",
  "lcd_cols": 16,
  "lcd_rows": 2,
  "max_consecutive_errors": 5
}
```

### Configuración de comandos WiFi

Archivo:

```text
/home/raspberry/wifi_command_config.json
```

Ejemplo:

```json
{
  "token": "CAMBIA_ESTE_TOKEN",
  "connect_script": "/home/raspberry/connect_wifi.sh"
}
```

### Configuración de apagado por GPIO

Archivo:

```text
/home/raspberry/gpio_shutdown_config.json
```

Ejemplo:

```json
{
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
```

## Prueba de la pantalla LCD

Antes de ejecutar los servicios completos, se puede probar la LCD con:

```bash
python3 src/test_lcd.py
```

Si la conexión I2C está correcta, la pantalla debe mostrar un mensaje de prueba.

## Ejecución manual

Modo BLE:

```bash
python3 src/ble_server.py
```

Modo Web:

```bash
python3 src/web_poll_display.py
```

Rutina GPIO:

```bash
python3 src/gpio_shutdown_watch.py
```

En instalación real se recomienda usar los servicios de `systemd`.

## Instalación en la Raspberry

Desde la carpeta del proyecto:

```bash
chmod +x scripts/*.sh
sudo ./scripts/install_display_project.sh
```

El instalador copia los archivos principales a `/home/raspberry/`, instala los servicios en `/etc/systemd/system/` y recarga `systemd`.

Después de instalar, editar los archivos de configuración reales:

```bash
nano /home/raspberry/web_config.json
nano /home/raspberry/wifi_command_config.json
nano /home/raspberry/gpio_shutdown_config.json
```

## Servicios systemd

El sistema usa cinco servicios principales:

```text
bt-agent-auto.service       → agente Bluetooth automático
ble-server.service          → modo BLE
web-display.service         → modo Web por polling
gpio-shutdown.service       → apagado físico por GPIO
display-mode-switch@.service → cambio de modo solicitado por otro servicio
```

### Activar modo BLE

```bash
sudo /home/raspberry/switch_display_mode.sh ble
```

Esto activa:

```text
bt-agent-auto.service
ble-server.service
gpio-shutdown.service
```

y detiene/deshabilita:

```text
web-display.service
```

### Activar modo Web

```bash
sudo /home/raspberry/switch_display_mode.sh web
```

Esto activa:

```text
web-display.service
gpio-shutdown.service
```

y detiene/deshabilita:

```text
bt-agent-auto.service
ble-server.service
```

### Detener modos de pantalla

```bash
sudo /home/raspberry/switch_display_mode.sh stop
```

### Revisar estado

```bash
/home/raspberry/switch_display_mode.sh status
```

Ejemplo de salida:

```text
Estado actual:
  bt-agent-auto.service    inactive
  ble-server.service       inactive
  web-display.service      active
  gpio-shutdown.service    active
```

## Logs y diagnóstico

Revisar modo BLE:

```bash
journalctl -u ble-server.service -n 80 --no-pager
```

Revisar modo Web:

```bash
journalctl -u web-display.service -n 80 --no-pager
```

Revisar GPIO:

```bash
journalctl -u gpio-shutdown.service -n 80 --no-pager
```

Ver logs en tiempo real:

```bash
journalctl -u web-display.service -f
```

Revisar servicios habilitados al inicio:

```bash
systemctl is-enabled web-display.service
systemctl is-enabled gpio-shutdown.service
systemctl is-enabled ble-server.service
systemctl is-enabled bt-agent-auto.service
```

## Comandos internos

### Cambiar de BLE a Web

Desde un cliente BLE enviar:

```text
web
```

o:

```text
wifi
```

### Cambiar de Web a BLE

Desde la página web enviar:

```text
ble
```

o:

```text
bluetooth
```

### Cambiar red WiFi desde BLE

Formato:

```text
wifi|TOKEN|SSID|PASSWORD
```

Ejemplo:

```text
wifi|TOKEN_PRIVADO|NombreRed|ClaveRed
```

Si el token es válido, la Raspberry intenta conectarse a la red usando `nmcli`. Si la conexión se realiza correctamente, muestra el estado en la LCD y cambia automáticamente al modo Web.

## Cliente BLE desde Windows

Para enviar mensajes BLE desde Windows se usa `tools/windows/send_ble.py`.

Instalar dependencia:

```powershell
pip install bleak
```

Enviar mensaje:

```powershell
python send_ble.py "hola"
```

Cambiar a modo Web:

```powershell
python send_ble.py "web"
```

Enviar comando WiFi:

```powershell
python send_ble.py "wifi|TOKEN|SSID|PASSWORD"
```

El script busca el dispositivo `RaspberryBLE`, intenta conectarse y escribe el mensaje en la característica RX del servicio BLE UART.

## Apagado por GPIO

El apagado físico usa los dos últimos pines del encabezado de 40 pines:

```text
Pin físico 39 → GND
Pin físico 40 → GPIO21 / BCM21
```

Lógica:

```text
Puente puesto   → funcionamiento normal
Puente retirado → inicia cuenta regresiva
```

Al retirar el puente, la LCD muestra:

```text
Seguro apagar?
Cuenta: 5
```

Si el puente se reconecta antes de terminar la cuenta regresiva, el apagado se cancela y la pantalla vuelve al contenido anterior.

Si la cuenta regresiva termina, la pantalla muestra:

```text
APAGANDO !!!
Espere...
```

Luego borra la LCD, detiene los servicios principales, ejecuta `sync` y solicita:

```bash
shutdown -h now
```

Al volver a encender la Raspberry, el puente debe estar puesto para evitar que el servicio interprete el estado abierto como una nueva orden de apagado.

## Notas de implementación y pruebas

El primer paso del montaje fue validar la pantalla LCD de forma independiente antes de integrarla con la comunicación inalámbrica. Para esto se usó una pantalla LCD 16x2 con módulo I2C basado en PCF8574, configurada en la dirección `0x27`. Esta prueba permitió confirmar que la Raspberry podía comunicarse correctamente con la pantalla por el bus I2C.

La comunicación BLE se implementó usando la interfaz Bluetooth integrada de la Raspberry Pi. No se trata de un puerto físico como USB o GPIO, sino de una interfaz de comunicación por radio disponible en la placa. Se eligió BLE porque permite una conexión directa con un celular o computador compatible y porque puede usarse desde clientes móviles o scripts en Windows.

El programa BLE trabaja con un servicio tipo UART. En términos prácticos, esto permite que el cliente escriba un mensaje y que la Raspberry lo reciba como una secuencia de bytes. Luego el programa convierte esos datos en texto, los limpia y los muestra en la pantalla LCD.

La actualización de la LCD se ejecuta en un hilo separado. Un hilo puede entenderse como una tarea que corre en paralelo dentro del mismo programa. Mientras una parte del código atiende la recepción de mensajes, otra parte mantiene actualizada la pantalla, incluyendo el desplazamiento horizontal de textos largos.

Como ambos procesos pueden usar la misma información —por ejemplo, historial, texto visible y posición del desplazamiento— se usa `threading.Lock`. Este bloqueo funciona como un candado: cuando una parte del programa modifica las variables compartidas, la otra espera. Esto evita que la pantalla lea datos incompletos o que un mensaje nuevo se mezcle con una actualización en curso.

La ejecución automática se resolvió mediante servicios `systemd`. Los archivos `.service` permiten que el sistema funcione sin abrir manualmente una terminal. En estos servicios se usan instrucciones como `After`, `Requires`, `Wants`, `Conflicts`, `Restart` y `ExecStartPre`. `After` define orden de arranque, `Requires` declara dependencias necesarias, `Wants` solicita servicios relacionados sin hacerlos estrictamente obligatorios y `Conflicts` evita que el modo BLE y el modo Web se ejecuten al mismo tiempo.

La instrucción `ExecStartPre=/bin/sleep 4` se usa para dar tiempo a que Bluetooth, la red o el bus I2C estén disponibles antes de iniciar los programas principales. También se agregó una limpieza previa de `lcd_override.lock` en los servicios de pantalla para evitar que un bloqueo temporal de la rutina GPIO deje la LCD sin actualizar después de un reinicio.

El modo Web se implementó por polling. La Raspberry consulta periódicamente la API y revisa si hay mensajes nuevos. Esta decisión evita exponer directamente la Raspberry a internet y permite que la página web funcione desde cualquier lugar, siempre que el hosting esté disponible y la Raspberry tenga acceso a internet.

El sistema Web usa un estado de actividad. Cada vez que la Raspberry consulta `poll.php`, el servidor actualiza la marca de último aviso. La página web consulta `status.php` para decidir si debe mostrar el formulario o indicar que la pantalla no está disponible.

La recuperación ante fallos se incorporó para evitar que la Raspberry quede atrapada en modo Web sin conexión. Si `web_poll_display.py` no logra consultar la API después de varios intentos consecutivos, muestra un aviso en la LCD y cambia automáticamente a modo BLE. Desde BLE se puede enviar una nueva red WiFi mediante un comando con token.

Para permitir cambios de modo desde programas que corren como usuario `raspberry`, se configuraron reglas limitadas en `sudoers`. No se otorgaron permisos generales de administrador; solo se permitió ejecutar los comandos específicos de cambio de modo y conexión WiFi. Esto reduce el riesgo frente a dar permisos `NOPASSWD` sin restricciones.

El apagado por GPIO se diseñó con lógica normalmente cerrada. El puente permanece conectado durante el funcionamiento normal. Al retirarlo, inicia una cuenta regresiva visible en la LCD. Esta decisión reduce apagados accidentales y permite cancelar el proceso simplemente reconectando el puente antes de que termine la cuenta.

Durante las pruebas se usaron `journalctl`, `systemctl status`, `nmcli`, `i2cdetect`, `ssh` y pruebas manuales desde BLE y desde la página web. La depuración fue progresiva: primero LCD, luego BLE, después Web/API, posteriormente cambio de modos, reconexión WiFi, fallback a BLE y apagado seguro por GPIO.

## Estado del proyecto

El proyecto fue probado en Raspberry Pi con pantalla LCD 16x2 I2C, comunicación BLE, página web pública, API PHP/MySQL, cambio automático de modos, reconexión WiFi desde BLE y apagado físico seguro por GPIO.

El sistema actual permite recibir mensajes desde BLE o desde una página web, mostrar los mensajes en la LCD, cambiar entre modos de operación, recuperar la conexión cuando falla el modo Web y apagar la Raspberry de forma segura sin entrar por consola.
