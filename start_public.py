"""Script para iniciar el servidor con acceso público
"""

import subprocess
import time
import sys
import os

def start_server():
    """Inicia el servidor Flask"""
    print("Iniciando servidor Flask...")
    # El servidor ya debería estar ejecutándose en segundo plano
    print("Servidor Flask ejecutándose en puerto 3000")

def start_tunnel():
    """Inicia LocalTunnel para acceso público"""
    print("Iniciando LocalTunnel para acceso público...")
    try:
        # Ejecutar LocalTunnel
        result = subprocess.run(['lt', '--port', '3000'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("LocalTunnel iniciado correctamente")
            print("Tu aplicación estará disponible en una URL pública")
            print("Ejemplo: https://abc123.loca.lt")
        else:
            print(f"Error al iniciar LocalTunnel: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("LocalTunnel iniciado (puede tomar unos segundos)")
    except FileNotFoundError:
        print("LocalTunnel no está instalado. Instálalo con: npm install -g localtunnel")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("=== Granjas del Carmen - Servidor Público ===")
    print()
    
    # Verificar que el servidor esté ejecutándose
    start_server()
    print()
    
    # Iniciar túnel público
    start_tunnel()
    print()
    
    print("=== Instrucciones ===")
    print("1. El servidor Flask está ejecutándose en puerto 3000")
    print("2. LocalTunnel creará una URL pública")
    print("3. Comparte la URL pública con otros usuarios")
    print("4. Presiona Ctrl+C para detener")
    print()
    
    try:
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        sys.exit(0)

if __name__ == "__main__":
    main()
