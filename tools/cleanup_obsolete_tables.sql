-- Script para eliminar tablas obsoletas que ya no se usan
-- Estas tablas fueron reemplazadas por la tabla unificada 'animals' y 'animal_sales'
-- 
-- IMPORTANTE: Ejecutar este script SOLO después de verificar que:
-- 1. Todos los datos importantes han sido migrados a las tablas nuevas
-- 2. No hay dependencias activas en estas tablas
-- 3. Se ha hecho un backup de la base de datos
--
-- Tablas a eliminar:
-- - rabbits (reemplazada por animals con species='RABBIT')
-- - cows (reemplazada por animals con species='COW')
-- - sheep (reemplazada por animals con species='SHEEP')
-- - rabbit_sales (reemplazada por animal_sales con animal_type='RABBIT')

-- Verificar que las tablas existen antes de eliminarlas
DO $$
BEGIN
    -- Eliminar tabla rabbit_sales si existe
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'rabbit_sales') THEN
        DROP TABLE IF EXISTS rabbit_sales CASCADE;
        RAISE NOTICE 'Tabla rabbit_sales eliminada';
    ELSE
        RAISE NOTICE 'Tabla rabbit_sales no existe, omitiendo';
    END IF;

    -- Eliminar tabla rabbits si existe
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'rabbits') THEN
        DROP TABLE IF EXISTS rabbits CASCADE;
        RAISE NOTICE 'Tabla rabbits eliminada';
    ELSE
        RAISE NOTICE 'Tabla rabbits no existe, omitiendo';
    END IF;

    -- Eliminar tabla cows si existe
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cows') THEN
        DROP TABLE IF EXISTS cows CASCADE;
        RAISE NOTICE 'Tabla cows eliminada';
    ELSE
        RAISE NOTICE 'Tabla cows no existe, omitiendo';
    END IF;

    -- Eliminar tabla sheep si existe
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sheep') THEN
        DROP TABLE IF EXISTS sheep CASCADE;
        RAISE NOTICE 'Tabla sheep eliminada';
    ELSE
        RAISE NOTICE 'Tabla sheep no existe, omitiendo';
    END IF;

    RAISE NOTICE 'Limpieza de tablas obsoletas completada';
END $$;

