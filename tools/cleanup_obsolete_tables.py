"""
Script para eliminar tablas obsoletas que ya no se usan.
Estas tablas fueron reemplazadas por la tabla unificada 'animals' y 'animal_sales'.

IMPORTANTE: Ejecutar este script SOLO después de verificar que:
1. Todos los datos importantes han sido migrados a las tablas nuevas
2. No hay dependencias activas en estas tablas
3. Se ha hecho un backup de la base de datos

Tablas a eliminar:
- rabbits (reemplazada por animals con species='RABBIT')
- cows (reemplazada por animals con species='COW')
- sheep (reemplazada por animals con species='SHEEP')
- rabbit_sales (reemplazada por animal_sales con animal_type='RABBIT')
"""
from sqlalchemy import text
from app.utils.database import engine

def cleanup_obsolete_tables():
    """Eliminar tablas obsoletas que ya no se usan"""
    obsolete_tables = ['rabbit_sales', 'rabbits', 'cows', 'sheep']
    
    with engine.begin() as conn:
        for table_name in obsolete_tables:
            try:
                # Verificar si la tabla existe
                check_query = text(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = :table_name
                    )
                """)
                result = conn.execute(check_query, {'table_name': table_name})
                exists = result.scalar()
                
                if exists:
                    # Eliminar la tabla con CASCADE para eliminar también dependencias
                    drop_query = text(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    conn.execute(drop_query)
                    print(f"[OK] Tabla '{table_name}' eliminada exitosamente")
                else:
                    print(f"[INFO] Tabla '{table_name}' no existe, omitiendo")
            except Exception as e:
                print(f"[ERROR] Error al eliminar tabla '{table_name}': {e}")
    
    print("\n[OK] Limpieza de tablas obsoletas completada")

if __name__ == "__main__":
    import sys
    
    # Confirmación antes de ejecutar
    print("ADVERTENCIA: Este script eliminara las siguientes tablas:")
    print("   - rabbit_sales")
    print("   - rabbits")
    print("   - cows")
    print("   - sheep")
    
    # Si se pasa --confirm como argumento, ejecutar directamente
    if len(sys.argv) > 1 and sys.argv[1] == '--confirm':
        print("\nConfirmacion recibida. Ejecutando limpieza...")
        cleanup_obsolete_tables()
    else:
        print("\nEstas seguro de que deseas continuar? (si/no): ", end='')
        try:
            confirmation = input().strip().lower()
            
            if confirmation in ['si', 'yes', 'y', 's']:
                cleanup_obsolete_tables()
            else:
                print("Operacion cancelada")
                sys.exit(0)
        except EOFError:
            print("\nNo se puede leer input interactivo. Usa --confirm para ejecutar directamente.")
            print("Ejemplo: python cleanup_obsolete_tables.py --confirm")
            sys.exit(1)

