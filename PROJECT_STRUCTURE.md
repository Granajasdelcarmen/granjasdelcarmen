# Granjas del Carmen - Estructura del Proyecto

## 📁 Estructura de Carpetas

```
granjasdelcarmen/
├── app/                          # Paquete principal de la aplicación
│   ├── __init__.py              # Factory de la aplicación Flask
│   ├── api/                     # API endpoints
│   │   ├── __init__.py
│   │   └── v1/                  # API versión 1
│   │       ├── __init__.py      # Configuración de API v1
│   │       ├── auth_controller.py    # Controlador de autenticación
│   │       ├── user_controller.py    # Controlador de usuarios
│   │       └── rabbit_controller.py  # Controlador de conejos
│   ├── config/                  # Configuración
│   │   ├── __init__.py
│   │   └── settings.py          # Configuraciones de la aplicación
│   ├── repositories/            # Patrón Repository para base de datos
│   │   ├── __init__.py
│   │   ├── base.py             # Repository base
│   │   ├── user_repository.py  # Repository de usuarios
│   │   └── rabbit_repository.py # Repository de conejos
│   ├── services/               # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── user_service.py     # Servicio de usuarios
│   │   └── rabbit_service.py   # Servicio de conejos
│   └── utils/                  # Utilidades comunes
│       ├── __init__.py
│       ├── database.py         # Utilidades de base de datos
│       ├── validators.py       # Validadores comunes
│       └── response.py         # Utilidades de respuesta
├── alembic/                    # Migraciones de base de datos
├── templates/                  # Plantillas HTML
├── models.py                   # Modelos de SQLAlchemy
├── server.py                   # Punto de entrada principal
├── requirements.txt           # Dependencias
└── PROJECT_STRUCTURE.md       # Este archivo
```

## 🏗️ Arquitectura

### **Patrón de Arquitectura: Clean Architecture + Repository Pattern**

1. **Controllers** (`app/api/v1/`): Manejan las peticiones HTTP y respuestas
2. **Services** (`app/services/`): Contienen la lógica de negocio
3. **Repositories** (`app/repositories/`): Manejan el acceso a datos
4. **Utils** (`app/utils/`): Utilidades comunes y helpers
5. **Config** (`app/config/`): Configuraciones de la aplicación

### **Principios Aplicados:**

- **Single Responsibility**: Cada clase tiene una responsabilidad específica
- **Dependency Injection**: Los servicios reciben sus dependencias
- **Separation of Concerns**: Separación clara entre capas
- **DRY (Don't Repeat Yourself)**: Eliminación de código duplicado
- **SOLID Principles**: Aplicación de principios SOLID

## 🚀 Beneficios de la Nueva Estructura

### **Escalabilidad**
- Fácil agregar nuevas funcionalidades
- Estructura modular y organizada
- Separación clara de responsabilidades

### **Mantenibilidad**
- Código más limpio y organizado
- Fácil localización de funcionalidades
- Patrones consistentes

### **Testabilidad**
- Servicios independientes fáciles de testear
- Inyección de dependencias para mocking
- Separación clara de responsabilidades

### **Reutilización**
- Utilidades comunes reutilizables
- Patrones base para nuevos repositorios
- Servicios modulares

## 📋 Cómo Usar

### **Ejecutar la Aplicación:**
```bash
python server.py
```

### **Documentación API:**
- Swagger UI: `http://localhost:3000/api/v1/docs/`
- Home: `http://localhost:3000/`

### **Agregar Nueva Funcionalidad:**

1. **Crear Repository** (si es necesario):
   ```python
   # app/repositories/nuevo_repository.py
   class NuevoRepository(BaseRepository[NuevoModel]):
       # Implementar métodos específicos
   ```

2. **Crear Service**:
   ```python
   # app/services/nuevo_service.py
   class NuevoService:
       # Implementar lógica de negocio
   ```

3. **Crear Controller**:
   ```python
   # app/api/v1/nuevo_controller.py
   class NuevoController(Resource):
       # Implementar endpoints
   ```

4. **Registrar en API**:
   ```python
   # app/api/v1/__init__.py
   # Agregar namespace y importar controller
   ```

## 🔧 Configuración

### **Variables de Entorno:**
```env
FLASK_ENV=development
APP_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./dev.db
AUTH0_DOMAIN=your-auth0-domain
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
HOST=0.0.0.0
PORT=3000
DEBUG=True
```

## 📊 Comparación: Antes vs Después

### **Antes:**
- Todo en un archivo (`server.py` - 472 líneas)
- Código duplicado
- Responsabilidades mezcladas
- Difícil de mantener y escalar

### **Después:**
- Estructura modular organizada
- Separación clara de responsabilidades
- Código reutilizable
- Fácil de mantener y escalar
- Patrones de diseño aplicados
- Código más limpio y profesional
