"""Script de configuración para nuevos desarrolladores
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🔄 {description}")
    print(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print("✅ Completado exitosamente")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_requirements():
    """Verifica que los archivos necesarios existan"""
    required_files = [
        'requirements.txt',
        'server.py', 
        'models.py',
        'alembic.ini',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Archivos faltantes: {missing_files}")
        return False
    
    print("✅ Todos los archivos necesarios están presentes")
    return True

def main():
    print("🚀 Configuración para Desarrolladores - Granjas del Carmen")
    print("=" * 60)
    
    # Verificar archivos necesarios
    if not check_requirements():
        print("\n❌ Configuración incompleta. Asegúrate de tener todos los archivos.")
        return
    
    # 1. Instalar dependencias
    if not run_command("pip install -r requirements.txt", 
                      "Instalando dependencias de Python"):
        print("❌ Error instalando dependencias")
        return
    
    # 2. Verificar conexión a base de datos
    print("\n🔍 Verificando conexión a base de datos...")
    if not run_command("python -c \"from models import Base; print('Conexión OK')\"", 
                      "Probando conexión a base de datos"):
        print("❌ Error de conexión a base de datos")
        print("Verifica tu archivo .env con las credenciales correctas")
        return
    
    # 3. Sincronizar migraciones
    print("\n📊 Opciones de sincronización:")
    print("1. Aplicar migraciones (mantener datos locales)")
    print("2. Reset completo (borrar datos locales)")
    print("3. Solo verificar estado")
    
    choice = input("\nSelecciona una opción (1-3): ").strip()
    
    if choice == "1":
        run_command("python -m alembic upgrade head", 
                   "Aplicando migraciones")
    elif choice == "2":
        print("⚠️  ADVERTENCIA: Esto borrará todos los datos locales")
        confirm = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
        if confirm == "SI":
            run_command("python -m alembic downgrade base", 
                       "Revirtiendo migraciones")
            run_command("python -m alembic upgrade head", 
                       "Aplicando migraciones")
        else:
            print("Operación cancelada")
    elif choice == "3":
        run_command("python -m alembic current", 
                   "Verificando estado actual")
    else:
        print("Opción no válida")
        return
    
    # 4. Verificar estado final
    print("\n✅ Verificación final:")
    run_command("python -m alembic current", "Estado de migraciones")
    
    print("\n🎉 ¡Configuración completada!")
    print("\nPara ejecutar el servidor:")
    print("python server.py")

if __name__ == "__main__":
    main()
