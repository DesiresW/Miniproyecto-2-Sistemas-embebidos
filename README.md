# Miniproyecto 2 - Sistemas Embebidos

## Autores

- Jose Miguel Sánchez Vargas
- Juan Pablo Prieto Vergara
- Vladimir Enrique Alvarez

## Descripción

Este proyecto implementa una pantalla remota con Raspberry Pi y LCD 16x2 I2C. El sistema puede recibir mensajes por dos vías: Bluetooth Low Energy (BLE) o una página web pública. Los mensajes se muestran en la LCD, conservando el historial visible de las dos últimas entradas.

El montaje evolucionó desde una comunicación BLE básica hacia un sistema multimodo con servicios de Linux, conmutación entre modos, recuperación ante fallos de internet, configuración de WiFi por BLE y apagado físico seguro por GPIO.

## Arquitectura general

```text
Modo BLE:
PC o celular BLE → Raspberry Pi → LCD 16x2 I2C

Modo Web:
Página web → API PHP/MySQL → Raspberry Pi por polling → LCD 16x2 I2C

Control físico:
Puente GPIO21-GND → cuenta regresiva en LCD → shutdown seguro
```

## Funciones principales

- Recepción de mensajes por Bluetooth Low Energy.
- Recepción de mensajes desde una página web pública.
- API en PHP/MySQL para guardar mensajes y reportar si la Raspberry está activa.
- Polling desde la Raspberry hacia el hosting.
- Cambio de modo por comando:
  - Desde Web: `ble` o `bluetooth`.
  - Desde BLE: `web` o `wifi`.
- Configuración de red WiFi desde BLE con el formato:
  - `wifi|TOKEN|SSID|PASSWORD`
- Fallback automático: si el modo Web no puede consultar la API varias veces, cambia a modo BLE.
- Apagado físico seguro:
  - Pin físico 39 = GND.
  - Pin físico 40 = GPIO21 / BCM21.
  - Puente puesto = funcionamiento normal.
  - Puente retirado = cuenta regresiva de apagado.
- Limpieza de pantalla antes de apagar.
- Servicios `systemd` para operación autónoma.

## Estructura del repositorio

```text
.
├── config/
│   ├── gpio_shutdown_config.example.json
│   ├── web_config.example.json
│   └── wifi_command_config.example.json
├── docs/
│   ├── comandos_actualizar_repo.md
│   └── memoria_tecnica.md
├── scripts/
│   ├── connect_wifi.sh
│   ├── diagnostico_display.sh
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
│   ├── schema.sql
│   ├── send_message.php
│   └── status.php
├── wordpress/
│   └── publica-mensaje.html
├── .gitignore
├── README.md
└── requirements.txt
```

## Archivos principales

`src/ble_server.py` ejecuta el modo BLE. Publica la Raspberry como periférico BLE tipo UART, recibe mensajes, actualiza la LCD y reconoce comandos internos de cambio de modo o configuración WiFi.

`src/web_poll_display.py` ejecuta el modo Web. Consulta periódicamente la API, muestra mensajes nuevos en la LCD y cambia automáticamente a BLE si falla la conexión con el servidor.

`src/gpio_shutdown_watch.py` mantiene activo el apagado físico. Lee GPIO21, toma control temporal de la LCD con una cuenta regresiva y ejecuta `shutdown -h now` si el puente no se reconecta.

`scripts/switch_display_mode.sh` cambia entre modo BLE y modo Web. Activa y desactiva los servicios necesarios para evitar que dos procesos escriban la LCD al mismo tiempo.

`scripts/connect_wifi.sh` conecta la Raspberry a una red WiFi usando `nmcli`. Recibe SSID y contraseña por entrada estándar para no exponer la clave como argumento visible.

`web_api/` contiene la API PHP/MySQL usada por la página y por la Raspberry.

`wordpress/publica-mensaje.html` contiene el bloque HTML, CSS y JavaScript para pegar en WordPress como “HTML personalizado”.

## Requisitos

Hardware:

- Raspberry Pi con Bluetooth y WiFi.
- Pantalla LCD 16x2 con módulo I2C basado en PCF8574.
- Puente hembra-hembra de 2.54 mm para GPIO21-GND.
- Conexión a internet para el modo Web.

Dependencias del sistema:

```bash
sudo apt update
sudo apt install -y python3 python3-pip bluetooth bluez bluez-tools i2c-tools python3-requests python3-gpiozero python3-lgpio network-manager
```

Dependencias de Python cuando se instalan con `pip`:

```bash
pip3 install bluezero RPLCD smbus2 requests gpiozero
```

En Raspberry Pi OS puede ser necesario instalar algunas librerías con `apt` o usar entorno virtual, dependiendo de la política de Python del sistema.

## Habilitar I2C

```bash
sudo raspi-config
```

Activar I2C en las opciones de interfaz y reiniciar si es necesario.

Verificar dirección de la LCD:

```bash
i2cdetect -y 1
```

En este montaje se usó la dirección `0x27`.

## Instalación en la Raspberry

Copiar el repositorio a la Raspberry, por ejemplo:

```bash
scp -r . raspberry@192.168.1.52:/home/raspberry/raspberry-display-modes
```

Entrar por SSH:

```bash
ssh raspberry@192.168.1.52
```

Instalar:

```bash
cd /home/raspberry/raspberry-display-modes
chmod +x scripts/*.sh
sudo ./scripts/install_display_project.sh
```

Editar configuración Web:

```bash
nano /home/raspberry/web_config.json
```

Editar token de comandos WiFi por BLE:

```bash
nano /home/raspberry/wifi_command_config.json
```

## Configuración del hosting

1. Crear una base de datos MySQL.
2. Ejecutar `web_api/schema.sql`.
3. Subir los archivos PHP a una carpeta pública, por ejemplo `/api`.
4. Copiar `config.example.php` como `config.php`.
5. Completar credenciales de base de datos y token de Raspberry.

Pruebas esperadas:

```text
https://TU_DOMINIO/api/status.php
https://TU_DOMINIO/api/poll.php?token=TU_TOKEN&last_id=0
```

`send_message.php` debe probarse por POST.

## Página WordPress

Crear una página plana o tipo landing page y pegar el contenido de:

```text
wordpress/publica-mensaje.html
```

en un bloque de “HTML personalizado”.

La página consulta `status.php` cada cinco segundos. Si la Raspberry está activa, muestra el formulario; si no, oculta el envío.

## Uso de modos

Ver estado:

```bash
/home/raspberry/switch_display_mode.sh status
```

Activar modo Web:

```bash
sudo /home/raspberry/switch_display_mode.sh web
```

Activar modo BLE:

```bash
sudo /home/raspberry/switch_display_mode.sh ble
```

Detener ambos modos de pantalla:

```bash
sudo /home/raspberry/switch_display_mode.sh stop
```

El servicio de apagado por GPIO permanece activo en ambos modos.

## Comandos internos

Desde la página web:

```text
ble
bluetooth
```

Cambian el sistema a modo BLE.

Desde BLE:

```text
web
wifi
```

Cambian el sistema a modo Web.

Desde BLE también se puede cambiar la red WiFi:

```text
wifi|TOKEN|SSID|PASSWORD
```

Si la conexión WiFi se logra, el sistema cambia automáticamente a modo Web.

## Enviar mensajes BLE desde Windows

Instalar `bleak`:

```powershell
pip install bleak
```

Usar:

```powershell
python tools\windows\send_ble.py "hola"
python tools\windows\send_ble.py "web"
python tools\windows\send_ble.py "wifi|TOKEN|SSID|PASSWORD"
```

## Apagado físico por GPIO

Conexión:

```text
Pin físico 39 = GND
Pin físico 40 = GPIO21 / BCM21
```

Funcionamiento:

```text
Puente puesto   = normal
Puente retirado = cuenta regresiva
Puente reconectado antes del final = se cancela apagado
Cuenta terminada = APAGANDO !!!, limpia LCD y ejecuta shutdown
```

Después del apagado, volver a poner el puente antes de alimentar de nuevo la Raspberry.

## Logs y diagnóstico

Logs principales:

```bash
journalctl -u web-display.service -n 80 --no-pager
journalctl -u ble-server.service -n 80 --no-pager
journalctl -u gpio-shutdown.service -n 80 --no-pager
journalctl -u bt-agent-auto.service -n 80 --no-pager
```

Exportar diagnóstico:

```bash
/home/raspberry/diagnostico_display.sh
```

Descargar desde Windows:

```powershell
scp raspberry@192.168.1.52:/home/raspberry/diagnostico_display_*.tar.gz .
```

## Estado actual del proyecto

El sistema quedó probado con:

- Modo Web activo por defecto.
- Cambio Web → BLE por mensaje `ble`.
- Cambio BLE → Web por mensaje `web`.
- Cambio de red WiFi desde BLE.
- Fallback Web → BLE por error de API.
- Apagado físico por GPIO con cuenta regresiva.
- Limpieza de LCD antes de apagado.
- Servicios `systemd` con conflictos entre modos para evitar escritura simultánea en la pantalla.

## Descripción corta para GitHub

Sistema embebido con Raspberry Pi, LCD 16x2 I2C, comunicación BLE y Web, cambio automático de modos, configuración WiFi por BLE y apagado seguro por GPIO.
