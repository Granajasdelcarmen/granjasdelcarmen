# 🚀 Guía de Configuración para Desarrolladores

## 📋 Pasos para Sincronizar con los Cambios

### **1. Obtener los cambios del repositorio**
```bash
git pull origin main
```

### **2. Configuración automática (Recomendado)**
```bash
python setup_dev.py
```

### **3. Configuración manual**

#### **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

#### **Configurar variables de entorno:**
- Copia `.env.example` a `.env` (si existe)
- O crea tu archivo `.env` con las credenciales de base de datos

#### **Sincronizar base de datos:**

**Opción A: Mantener datos locales**
```bash
python -m alembic upgrade head
```

**Opción B: Reset completo (CUIDADO: borra datos locales)**
```bash
python -m alembic downgrade base
python -m alembic upgrade head
```

## 🔧 Comandos Útiles

### **Ver estado de migraciones:**
```bash
python -m alembic current
```

### **Ver historial de migraciones:**
```bash
python -m alembic history
```

### **Ejecutar servidor:**
```bash
python server.py
```

## ⚠️ Notas Importantes

1. **Siempre haz backup** de tu base de datos antes de hacer cambios
2. **Verifica tu archivo .env** tiene las credenciales correctas
3. **Si hay conflictos**, contacta al equipo antes de hacer cambios

## 🆘 Solución de Problemas

### **Error: "relation does not exist"**
```bash
python -m alembic stamp head
```

### **Error: "connection refused"**
- Verifica tu archivo `.env`
- Asegúrate de que la base de datos esté accesible

### **Error: "migration out of sync"**
```bash
python -m alembic upgrade head
```

## 📞 Contacto

Si tienes problemas, contacta al equipo de desarrollo.
