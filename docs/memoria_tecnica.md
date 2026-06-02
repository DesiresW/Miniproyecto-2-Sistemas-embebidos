# Memoria técnica breve

El proyecto empezó como un receptor de mensajes BLE hacia una LCD 16x2 I2C. La versión actual integra tres capas de interacción:

1. Entrada local inalámbrica por BLE.
2. Entrada remota por página web, API PHP/MySQL y polling desde la Raspberry.
3. Control físico por GPIO para apagado seguro.

La Raspberry se comporta como un nodo embebido que puede operar en modo BLE o modo Web. Los modos se excluyen entre sí mediante servicios systemd con `Conflicts`, evitando que dos procesos controlen la LCD simultáneamente.

El modo Web tiene recuperación automática: si la API deja de responder, cambia a modo BLE para permitir reconfigurar WiFi desde un cliente BLE. El comando de red usa el formato `wifi|TOKEN|SSID|PASSWORD` y ejecuta `connect_wifi.sh` con permisos sudo limitados.

El apagado físico usa GPIO21 con lógica normalmente cerrada. El puente entre pin físico 39 y 40 indica operación normal. Al retirar el puente, se toma control temporal de la LCD, se muestra una cuenta regresiva y, si el puente no vuelve, se limpian los servicios y se ejecuta `shutdown -h now`.
