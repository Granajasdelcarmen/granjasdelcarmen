# 🚀 Guía de Despliegue en Vercel

Esta guía te ayudará a desplegar la aplicación Flask en Vercel.

## 📋 Requisitos Previos

1. Cuenta en Vercel
2. Base de datos PostgreSQL (Vercel no soporta SQLite en producción)
3. Variables de entorno configuradas

## 🔧 Configuración de Variables de Entorno en Vercel

Ve a tu proyecto en Vercel → Settings → Environment Variables y configura las siguientes variables:

### **Variables Requeridas:**

```env
# Base de datos (REQUERIDO - debe ser PostgreSQL)
# Formato básico:
DATABASE_URL=postgresql://user:password@host:port/database
# Con SSL (recomendado para producción):
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
# O para servicios como Supabase/Neon:
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=prefer

# Flask Configuration
APP_SECRET_KEY=tu-clave-secreta-super-segura-aqui
FLASK_ENV=production

# CORS Configuration (IMPORTANTE: debe coincidir con el dominio del frontend)
FRONTEND_URL=https://admin.granjasdelcarmen.com
# Si necesitas múltiples orígenes, sepáralos con comas:
# FRONTEND_URL=https://admin.granjasdelcarmen.com,https://www.granjasdelcarmen.com

# Auth0 (Opcional - solo si usas autenticación)
AUTH0_DOMAIN=tu-dominio.auth0.com
AUTH0_CLIENT_ID=tu-client-id
AUTH0_CLIENT_SECRET=tu-client-secret
```

### **Variables Opcionales:**

```env
DEBUG=False
HOST=0.0.0.0
PORT=3000
```

## 📁 Estructura de Archivos para Vercel

La aplicación ya está configurada con:

- ✅ `vercel.json` - Configuración de Vercel
- ✅ `api/index.py` - Punto de entrada para funciones serverless
- ✅ `requirements.txt` - Dependencias de Python

## 🚀 Pasos para Desplegar

### **Opción 1: Desde GitHub (Recomendado)**

1. Conecta tu repositorio a Vercel
2. Vercel detectará automáticamente la configuración
3. Asegúrate de configurar las variables de entorno antes del despliegue
4. Haz clic en "Deploy"

### **Opción 2: Desde CLI**

```bash
# Instalar Vercel CLI
npm i -g vercel

# Iniciar sesión
vercel login

# Desplegar
vercel

# Para producción
vercel --prod
```

## ⚠️ Problemas Comunes y Soluciones

### **Error: "Python process exited with exit status: 1"**

**Causas posibles:**
1. **Base de datos no configurada**: Asegúrate de que `DATABASE_URL` esté configurada y sea una URL de PostgreSQL válida
2. **Variables de entorno faltantes**: Verifica que todas las variables requeridas estén configuradas
3. **Dependencias faltantes**: Verifica que `requirements.txt` tenga todas las dependencias

**Solución:**
- Revisa los logs en Vercel Dashboard → Functions → Logs
- Verifica que `DATABASE_URL` apunte a una base de datos PostgreSQL accesible
- Asegúrate de que la base de datos tenga las tablas creadas (usa Alembic migrations)

### **Error: "FUNCTION_INVOCATION_FAILED"**

**Causas posibles:**
1. Error en la inicialización de la aplicación
2. Problema de conexión a la base de datos
3. Importación de módulos fallida

**Solución:**
- Revisa los logs detallados en Vercel
- Verifica que `api/index.py` esté correctamente configurado
- Asegúrate de que todas las rutas de importación sean correctas

### **Error de Conexión a Base de Datos**

**Solución:**
- Verifica que `DATABASE_URL` sea correcta
- Asegúrate de que la base de datos PostgreSQL esté accesible desde internet
- Verifica que el firewall permita conexiones desde Vercel
- Si usas un servicio como Supabase o Neon, verifica la configuración de SSL

### **Error: "invalid connection option 'check_same_thread'"**

Este error indica que se está intentando usar configuración de SQLite en PostgreSQL.

**Causas:**
- La variable `DATABASE_URL` no está configurada en Vercel
- La URL no tiene el formato correcto de PostgreSQL
- La detección automática del tipo de base de datos falló

**Solución:**
1. Verifica que `DATABASE_URL` esté configurada en Vercel
2. Asegúrate de que la URL comience con `postgresql://` o `postgres://`
3. Formato correcto: `postgresql://user:password@host:port/database`
4. Si necesitas SSL: `postgresql://user:password@host:port/database?sslmode=require`
5. Revisa los logs de Vercel para ver qué tipo de base de datos se detectó

## 🔍 Verificar el Despliegue

1. Ve a tu dashboard de Vercel
2. **Revisa los logs de RUNTIME** (no solo los de build):
   - Ve a tu proyecto en Vercel
   - Click en "Functions" → Selecciona `api/index.py`
   - Click en "Logs" para ver los logs de ejecución
   - Estos logs mostrarán errores específicos de inicialización
3. Prueba el endpoint de health: `https://tu-app.vercel.app/api/v1/health`
4. Verifica que las rutas de la API respondan correctamente

### **Cómo Revisar los Logs de Runtime:**

Los logs de **build** (que viste) solo muestran si el build fue exitoso. Los logs de **runtime** muestran qué pasa cuando la función se ejecuta:

1. En Vercel Dashboard → Tu Proyecto
2. Click en "Functions" (en el menú lateral)
3. Busca `api/index.py` en la lista
4. Click en "View Function Logs" o "Logs"
5. Ahí verás errores como:
   - Errores de importación
   - Errores de conexión a base de datos
   - Errores de inicialización de la app

## 📝 Notas Importantes

1. **SQLite no funciona en Vercel**: Debes usar PostgreSQL o similar
2. **Cold starts**: La primera solicitud puede tardar más (cold start)
3. **Timeouts**: Las funciones serverless tienen límites de tiempo (10s en plan gratuito)
4. **Base de datos**: Asegúrate de ejecutar las migraciones de Alembic antes del despliegue

## 🛠️ Migraciones de Base de Datos

Antes de desplegar, ejecuta las migraciones:

```bash
# Localmente, apuntando a la base de datos de producción
export DATABASE_URL=postgresql://...
python -m alembic upgrade head
```

O crea un script de migración que se ejecute automáticamente en el despliegue.

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en Vercel Dashboard
2. Verifica las variables de entorno
3. Prueba localmente con las mismas variables de entorno

