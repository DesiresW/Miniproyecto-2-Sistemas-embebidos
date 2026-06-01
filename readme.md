# Miniproyecto 2 - Sistemas Embebidos

## Autores

- Jose Miguel Sánchez Vargas
- Juan Pablo Prieto Vergara
- Vladimir Enrique Alvarez

## Descripción

Este proyecto implementa una comunicación inalámbrica básica entre un celular y una Raspberry Pi usando Bluetooth Low Energy (BLE). Los mensajes enviados desde el cliente BLE son recibidos por la Raspberry y mostrados en una pantalla LCD 16x2 conectada por I2C.

La idea del montaje se basa en usar la Raspberry como controlador, el Bluetooth como medio de comunicación inalámbrica y la pantalla LCD para la salida visual del mensaje.

## Objetivo

Recibir mensajes de forma inalámbrica en una Raspberry Pi y mostrarlos en una pantalla LCD 16x2, usando Python, BLE y comunicación I2C.

## Funcionamiento

Al iniciar, la Raspberry configura la pantalla LCD y publica un servicio BLE. Desde un celular o cliente compatible se puede establecer conexión y enviar mensajes de texto.

Cuando llega un mensaje, el programa lo limpia, actualiza el historial interno y lo muestra en la LCD. La pantalla conserva los dos mensajes más recientes. Si el texto supera el ancho de 16 caracteres, se desplaza horizontalmente para facilitar su lectura.

También se muestran eventos básicos del sistema, como conexión y desconexión del cliente Bluetooth.

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

Dependencias principales:

```bash
sudo apt update
sudo apt install python3-pip bluetooth bluez
pip3 install bluezero RPLCD smbus2
```

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

## Decisiones de implementación y pruebas

El primer paso del montaje fue validar la pantalla LCD de forma independiente antes de integrarla con la comunicación inalámbrica. Para esto se usó una pantalla LCD 16x2 con módulo I2C basado en PCF8574, configurada en la dirección `0x27`. Esta prueba permitió confirmar que la Raspberry podía comunicarse correctamente con la pantalla por el bus I2C antes de ejecutar el programa completo.

La comunicación inalámbrica se implementó usando la interfaz Bluetooth integrada de la Raspberry Pi. En este caso no se trata de un puerto físico como USB o GPIO, sino de una interfaz de comunicación por radio disponible en la placa. Se decidió usar Bluetooth Low Energy porque permite establecer una conexión directa con un celular, y en particular porque es compatible con el tipo de comunicación que puede utilizarse desde un iPhone mediante aplicaciones cliente BLE.

El programa principal trabaja con un servicio BLE tipo UART. En términos prácticos, esto permite que el celular escriba un mensaje y que la Raspberry lo reciba como una secuencia de datos. Luego el programa convierte esos datos en texto, los limpia y los muestra en la pantalla LCD. Esta lógica permitió cumplir el objetivo del miniproyecto: recibir información de forma inalámbrica y reflejarla en una salida física del sistema.

Una parte importante del funcionamiento está en la actualización de la pantalla. La LCD debe refrescarse constantemente, sobre todo cuando el mensaje es más largo que 16 caracteres y necesita desplazarse horizontalmente. Para que esa actualización no bloquee la recepción de mensajes BLE, se usó un hilo de ejecución separado. Un hilo puede entenderse como una tarea que corre en paralelo dentro del mismo programa: mientras una parte del código sigue atenta a los mensajes recibidos, otra parte se encarga de mantener actualizada la pantalla.

Como ambos procesos pueden usar la misma información —por ejemplo, el historial de mensajes, el texto visible y la posición del desplazamiento— fue necesario proteger esas variables compartidas. Para esto se usó un bloqueo con `threading.Lock`. El bloqueo funciona como un candado: cuando una parte del programa está modificando el historial o el texto que se muestra, la otra debe esperar. Esto evita que la pantalla lea información incompleta o que un mensaje nuevo se mezcle con una actualización en curso.

La ejecución automática se resolvió mediante servicios de `systemd`. El servicio principal, `ble-server.service`, se encarga de iniciar el programa de Python sin necesidad de abrir una terminal manualmente. Además, se configuró para depender de `bluetooth.service` y de `bt-agent-auto.service`, ya que el servidor BLE necesita que Bluetooth y el agente de conexión estén disponibles antes de iniciar. Por eso el archivo usa instrucciones como `Requires`, que declara dependencias necesarias, y `After`, que define el orden de arranque.

También se incluyó una espera inicial de cuatro segundos mediante `ExecStartPre=/bin/sleep 4`. Esta pausa evita que el programa arranque demasiado pronto, antes de que el sistema termine de preparar Bluetooth y los servicios asociados. En la práctica, esta pequeña espera ayudó a mejorar la estabilidad del arranque automático.

Durante las pruebas se revisó el comportamiento del sistema mediante los logs de `systemd`, especialmente con `journalctl`. Esto permitió confirmar si la pantalla había iniciado correctamente, si el servicio BLE se había publicado y si el programa seguía activo después de reiniciar la Raspberry. El proceso de depuración se hizo de forma progresiva: primero la LCD, luego el servidor BLE y finalmente la ejecución automática como servicio.

## Estado del proyecto

El proyecto fue probado en Raspberry Pi con una pantalla LCD 16x2 por I2C y ejecución automática mediante `systemd`.

El alcance actual cubre la recepción inalámbrica de mensajes y su visualización en pantalla. No incluye aplicación móvil propia, almacenamiento de mensajes ni autenticación avanzada.

