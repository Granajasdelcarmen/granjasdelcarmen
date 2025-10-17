# Script para iniciar el servidor con acceso público
# Granjas del Carmen

Write-Host "=== Granjas del Carmen - Servidor Público ===" -ForegroundColor Green
Write-Host ""

# Verificar que Python esté disponible
try {
    python --version
    Write-Host "Python encontrado" -ForegroundColor Green
} catch {
    Write-Host "Error: Python no encontrado" -ForegroundColor Red
    exit 1
}

# Verificar que LocalTunnel esté disponible
try {
    lt --help | Out-Null
    Write-Host "LocalTunnel encontrado" -ForegroundColor Green
} catch {
    Write-Host "Error: LocalTunnel no encontrado. Instálalo con: npm install -g localtunnel" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Iniciando servidor Flask..." -ForegroundColor Yellow
Write-Host "Servidor ejecutándose en puerto 3000" -ForegroundColor Yellow
Write-Host ""

Write-Host "Iniciando LocalTunnel para acceso público..." -ForegroundColor Yellow
Write-Host "Esto creará una URL pública que puedes compartir" -ForegroundColor Yellow
Write-Host ""

# Iniciar LocalTunnel
Write-Host "Ejecutando: lt --port 3000" -ForegroundColor Cyan
Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Red
Write-Host ""

lt --port 3000
