{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('ainara_raw', 'productos') }}
),

renamed as (
    select
        codigo as producto_id,
        categoria as categoria_id,
        nombre,
        descripcion,
        
        -- Precios delivery
        precio as precio_base,
        precio_efectivo,
        precio_mp as precio_mercadopago,
        precio_transferencia,
        precio_alianza,
        
        -- Precios mostrador
        precio_mostrador,
        precio_mostrador_efectivo,
        precio_mostrador_mp as precio_mostrador_mercadopago,
        precio_mostrador_transferencia,
        precio_mostrador_alianza,
        
        -- Descuento
        descuento as descuento_porcentaje,
        
        -- Configuración
        gustos as cantidad_gustos,
        dias as dias_disponible,
        mostrador as is_solo_mostrador,
        activo as is_activo,

        -- Peso en kg por tipo de producto
        case
            -- Packs especiales (más específicos primero)
            when lower(nombre) like '%pack 5 cucuruch%'         then 0   -- 5 × 0.2
            when lower(nombre) like '%pack 4 cucuruch%'         then 0   -- 4 × 0.2
            when lower(nombre) like '%4 de 1/2%'               then 2.0   -- 4 × 0.5
            when lower(nombre) like '%3 de 1/4%'               then 0.75  -- 3 × 0.25
            when lower(nombre) like '%1kg + 1/2%'              then 1.5   -- 1 + 0.5
            when lower(nombre) like '%2 x 1/4%'                then 0.5   -- 2 × 0.25
            -- Tamaños estándar (1 KG antes que 1/2 y 1/4)
            when lower(nombre) like '%1/2 kg%'
              or lower(nombre) like '%1/2kg%'                   then 0.5
            when lower(nombre) like '%1/4 kg%'
              or lower(nombre) like '%1/4kg%'                   then 0.25
            when lower(nombre) like '%3/4 kg%'
              or lower(nombre) like '%3/4kg%'                   then 0.75
            when nombre like '1 KG'
              or lower(nombre) like '1kg%'
              or lower(nombre) like '%promo 1kg%'
              or lower(nombre) like '%promo 1 kg%'              then 1.0
            -- Unidades individuales
            when lower(nombre) like '%capelina%'                then 0.25
            when lower(nombre) like '%vasito%'                  then 0.1
            when lower(nombre) like '%cucuruch%'                then 0.2
            -- Sin datos de peso (no helado o desconocido)
            else 0.0
        end as peso_kg,
        
        -- Timestamps
        to_timestamp(fecha_sys) as created_at,
        to_timestamp(last_fecha_update) as updated_at,
        admin_insert as created_by_admin_id,
        last_admin_update as updated_by_admin_id

    from source
    where codigo is not null
)

select * from renamed
