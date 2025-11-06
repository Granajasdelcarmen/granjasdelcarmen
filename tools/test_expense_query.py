"""
Script para probar la consulta de expenses usando el servicio
"""
from app.services.expense_service import ExpenseService

def test_expense_query():
    """Probar la consulta de expenses usando el servicio"""
    service = ExpenseService()
    
    print("Probando get_all_expenses()...")
    response_data, status_code = service.get_all_expenses()
    
    print(f"Status code: {status_code}")
    print(f"Response data type: {type(response_data)}")
    
    if isinstance(response_data, dict):
        print(f"Response data keys: {response_data.keys()}")
        if 'data' in response_data:
            print(f"Data type: {type(response_data['data'])}")
            print(f"Data length: {len(response_data['data']) if isinstance(response_data['data'], list) else 'N/A'}")
            print(f"Data: {response_data['data']}")
        if 'message' in response_data:
            print(f"Message: {response_data['message']}")
    else:
        print(f"Response data: {response_data}")

if __name__ == "__main__":
    try:
        test_expense_query()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


