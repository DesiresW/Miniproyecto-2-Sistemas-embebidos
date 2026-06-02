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
