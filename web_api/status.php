<?php
require_once __DIR__ . '/config.php';

$stmt = db()->prepare("
    SELECT
        id,
        nombre,
        ultimo_aviso,
        activo,
        TIMESTAMPDIFF(SECOND, ultimo_aviso, NOW()) AS segundos_desde_aviso
    FROM estado
    WHERE id = 1
    LIMIT 1
");
$stmt->execute();
$row = $stmt->fetch();

if (!$row || !$row['ultimo_aviso']) {
    json_response([
        'ok' => true,
        'online' => false,
        'message' => 'La pantalla no está disponible en este momento'
    ]);
}

$seconds = (int)$row['segundos_desde_aviso'];
$online = ((int)$row['activo'] === 1) && ($seconds <= ONLINE_TTL_SECONDS);

json_response([
    'ok' => true,
    'online' => $online,
    'last_seen' => $row['ultimo_aviso'],
    'seconds_since_last_seen' => $seconds
]);
