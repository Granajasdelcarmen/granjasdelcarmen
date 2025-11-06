"""
Script para verificar el rol de un usuario en la base de datos
"""
from sqlalchemy import text
from app.utils.database import engine

def check_user_role(user_id: str):
    """Verificar el rol de un usuario"""
    with engine.connect() as conn:
        # Verificar si el usuario existe
        check_user_query = text("""
            SELECT id, email, name, role, is_active
            FROM users
            WHERE id = :user_id
        """)
        result = conn.execute(check_user_query, {'user_id': user_id})
        user = result.fetchone()
        
        if not user:
            print(f"Usuario con ID '{user_id}' no encontrado en la base de datos")
            return
        
        print(f"Usuario encontrado:")
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Nombre: {user[2]}")
        print(f"  Rol: {user[3]}")
        print(f"  Activo: {user[4]}")
        
        role_lower = user[3].lower() if user[3] else ''
        if role_lower != 'admin':
            print(f"\nADVERTENCIA: El usuario NO tiene rol 'admin'")
            print(f"   Rol actual: '{user[3]}'")
            print(f"   Para acceder a /finance/expenses, el usuario debe tener rol 'admin'")
        else:
            print(f"\n[OK] El usuario tiene rol 'admin', puede acceder a /finance/expenses")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python check_user_role.py <user_id>")
        print("Ejemplo: python check_user_role.py 'google-oauth2|105070008073900975834'")
        sys.exit(1)
    
    user_id = sys.argv[1]
    check_user_role(user_id)

