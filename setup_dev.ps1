# Script de configuración para desarrolladores en Windows
# Granjas del Carmen

Write-Host "🚀 Configuración para Desarrolladores - Granjas del Carmen" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Verificar que Python esté instalado
try {
    $pythonVersion = python --version
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado. Instala Python primero." -ForegroundColor Red
    exit 1
}

# Verificar archivos necesarios
$requiredFiles = @('requirements.txt', 'server.py', 'models.py', 'alembic.ini')
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Archivos faltantes: $($missingFiles -join ', ')" -ForegroundColor Red
    Write-Host "Asegúrate de hacer 'git pull' primero" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Todos los archivos necesarios están presentes" -ForegroundColor Green

# Instalar dependencias
Write-Host "`n🔄 Instalando dependencias..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Dependencias instaladas correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error instalando dependencias" -ForegroundColor Red
    exit 1
}

# Verificar conexión a base de datos
Write-Host "`n🔍 Verificando conexión a base de datos..." -ForegroundColor Yellow
try {
    python -c "from models import Base; print('Conexión OK')"
    Write-Host "✅ Conexión a base de datos exitosa" -ForegroundColor Green
} catch {
    Write-Host "❌ Error de conexión a base de datos" -ForegroundColor Red
    Write-Host "Verifica tu archivo .env con las credenciales correctas" -ForegroundColor Yellow
    exit 1
}

# Opciones de sincronización
Write-Host "`n📊 Opciones de sincronización:" -ForegroundColor Cyan
Write-Host "1. Aplicar migraciones (mantener datos locales)" -ForegroundColor White
Write-Host "2. Reset completo (borrar datos locales)" -ForegroundColor White
Write-Host "3. Solo verificar estado" -ForegroundColor White

$choice = Read-Host "`nSelecciona una opción (1-3)"

switch ($choice) {
    "1" {
        Write-Host "`n🔄 Aplicando migraciones..." -ForegroundColor Yellow
        python -m alembic upgrade head
        Write-Host "✅ Migraciones aplicadas" -ForegroundColor Green
    }
    "2" {
        Write-Host "`n⚠️  ADVERTENCIA: Esto borrará todos los datos locales" -ForegroundColor Red
        $confirm = Read-Host "¿Estás seguro? (escribe 'SI' para confirmar)"
        if ($confirm -eq "SI") {
            Write-Host "🔄 Revirtiendo migraciones..." -ForegroundColor Yellow
            python -m alembic downgrade base
            Write-Host "🔄 Aplicando migraciones..." -ForegroundColor Yellow
            python -m alembic upgrade head
            Write-Host "✅ Reset completo realizado" -ForegroundColor Green
        } else {
            Write-Host "Operación cancelada" -ForegroundColor Yellow
        }
    }
    "3" {
        Write-Host "`n🔍 Verificando estado..." -ForegroundColor Yellow
        python -m alembic current
    }
    default {
        Write-Host "Opción no válida" -ForegroundColor Red
        exit 1
    }
}

# Verificación final
Write-Host "`n✅ Verificación final:" -ForegroundColor Green
python -m alembic current

Write-Host "`n🎉 ¡Configuración completada!" -ForegroundColor Green
Write-Host "`nPara ejecutar el servidor:" -ForegroundColor Cyan
Write-Host "python server.py" -ForegroundColor White
