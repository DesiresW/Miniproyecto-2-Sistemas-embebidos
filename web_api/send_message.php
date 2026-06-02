<?php
require_once __DIR__ . '/config.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['ok' => false, 'error' => 'Método no permitido'], 405);
}

$input = json_decode(file_get_contents('php://input'), true);
$mensaje = $input['mensaje'] ?? $_POST['mensaje'] ?? '';
$mensaje = clean_message($mensaje);

if ($mensaje === '') {
    json_response(['ok' => false, 'error' => 'El mensaje está vacío'], 400);
}

$stmt = db()->prepare('INSERT INTO mensajes (mensaje) VALUES (:mensaje)');
$stmt->execute(['mensaje' => $mensaje]);

json_response([
    'ok' => true,
    'id' => (int)db()->lastInsertId(),
    'mensaje' => $mensaje
]);
