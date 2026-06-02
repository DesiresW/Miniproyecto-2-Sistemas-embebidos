# Comandos para actualizar el repositorio

## 1. Entrar a la carpeta del repositorio local

```powershell
cd C:\Users\josem\Documents\Embebidos\raaspberry\WIFI\Miniproyecto-2-Sistemas-embebidos
```

## 2. Copiar o reemplazar archivos

Descomprimir el paquete actualizado y copiar su contenido sobre el repositorio local.

En PowerShell, si el paquete descomprimido está en `C:\Users\josem\Downloads\Miniproyecto-2-Sistemas-embebidos-actualizado`:

```powershell
Copy-Item -Path "C:\Users\josem\Downloads\Miniproyecto-2-Sistemas-embebidos-actualizado\*" -Destination "." -Recurse -Force
```

## 3. Revisar estado

```powershell
git status
```

## 4. Agregar cambios

```powershell
git add README.md .gitignore requirements.txt src systemd scripts config web_api wordpress tools docs
```

## 5. Crear commit

```powershell
git commit -m "Actualiza sistema multimodo BLE Web GPIO"
```

## 6. Subir a GitHub

```powershell
git push origin main
```

Si el repositorio local usa `master`:

```powershell
git push origin master
```

## 7. Verificar remoto

```powershell
git remote -v
git branch
```

## 8. Comando rápido completo

```powershell
git status
git add README.md .gitignore requirements.txt src systemd scripts config web_api wordpress tools docs
git commit -m "Actualiza sistema multimodo BLE Web GPIO"
git push origin main
```
