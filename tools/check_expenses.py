"""
Script para verificar datos en la tabla expenses
"""
from sqlalchemy import text
from app.utils.database import engine

def check_expenses():
    """Verificar datos en la tabla expenses"""
    with engine.connect() as conn:
        # Verificar si la tabla existe
        check_table_query = text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = 'expenses'
            )
        """)
        result = conn.execute(check_table_query)
        table_exists = result.scalar()
        
        print(f"Tabla 'expenses' existe: {table_exists}")
        
        if not table_exists:
            print("ERROR: La tabla 'expenses' no existe en la base de datos")
            return
        
        # Contar registros
        count_query = text("SELECT COUNT(*) FROM expenses")
        result = conn.execute(count_query)
        count = result.scalar()
        
        print(f"\nTotal de registros en 'expenses': {count}")
        
        if count > 0:
            # Obtener todos los registros
            select_query = text("""
                SELECT 
                    id,
                    category,
                    description,
                    amount,
                    expense_date,
                    vendor,
                    notes,
                    created_by,
                    created_at,
                    updated_at
                FROM expenses
                ORDER BY expense_date DESC
            """)
            result = conn.execute(select_query)
            expenses = result.fetchall()
            
            print("\nRegistros encontrados:")
            print("-" * 80)
            for expense in expenses:
                print(f"ID: {expense[0]}")
                print(f"  Categoría: {expense[1]}")
                print(f"  Descripción: {expense[2]}")
                print(f"  Monto: {expense[3]}")
                print(f"  Fecha: {expense[4]}")
                print(f"  Proveedor: {expense[5] or 'N/A'}")
                print(f"  Notas: {expense[6] or 'N/A'}")
                print(f"  Creado por: {expense[7]}")
                print(f"  Creado en: {expense[8]}")
                print(f"  Actualizado en: {expense[9]}")
                print("-" * 80)
        else:
            print("\nNo hay registros en la tabla 'expenses'")
        
        # Verificar estructura de la tabla
        print("\n\nEstructura de la tabla 'expenses':")
        structure_query = text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'expenses'
            ORDER BY ordinal_position
        """)
        result = conn.execute(structure_query)
        columns = result.fetchall()
        
        print("-" * 80)
        for col in columns:
            print(f"{col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3] or 'N/A'})")
        print("-" * 80)

if __name__ == "__main__":
    try:
        check_expenses()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


