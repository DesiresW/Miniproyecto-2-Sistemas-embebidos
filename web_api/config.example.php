<?php
// Copiar este archivo como config.php y completar credenciales reales.

define('DB_HOST', 'localhost');
define('DB_NAME', 'NOMBRE_BASE_DE_DATOS');
define('DB_USER', 'USUARIO_BASE_DE_DATOS');
define('DB_PASS', 'PASSWORD_BASE_DE_DATOS');

define('RASPBERRY_TOKEN', 'CAMBIA_ESTE_TOKEN');
define('ONLINE_TTL_SECONDS', 15);

function json_response($data, $status = 200) {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function db() {
    static $pdo = null;

    if ($pdo === null) {
        $dsn = 'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4';
        try {
            $pdo = new PDO($dsn, DB_USER, DB_PASS, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ]);
        } catch (Exception $e) {
            json_response(['ok' => false, 'error' => 'No se pudo conectar a la base de datos'], 500);
        }
    }

    return $pdo;
}

function clean_message($message) {
    $message = trim((string)$message);
    $message = strip_tags($message);
    $message = preg_replace('/\s+/u', ' ', $message);
    return mb_substr($message, 0, 160, 'UTF-8');
}
