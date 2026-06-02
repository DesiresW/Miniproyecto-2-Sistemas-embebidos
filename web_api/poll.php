<?php
require_once __DIR__ . '/config.php';

$token = $_GET['token'] ?? '';

if (!hash_equals(RASPBERRY_TOKEN, $token)) {
    json_response(['ok' => false, 'error' => 'Token inválido'], 403);
}

$last_id = isset($_GET['last_id']) ? (int)$_GET['last_id'] : 0;

$stmt = db()->prepare("
    UPDATE estado
    SET ultimo_aviso = NOW(), activo = 1
    WHERE id = 1
");
$stmt->execute();

$stmt = db()->prepare("
    SELECT id, mensaje, creado_en
    FROM mensajes
    WHERE id > :last_id
    ORDER BY id ASC
    LIMIT 1
");
$stmt->execute(['last_id' => $last_id]);
$message = $stmt->fetch();

json_response([
    'ok' => true,
    'online' => true,
    'message' => $message ?: null
]);
