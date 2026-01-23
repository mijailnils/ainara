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
        
        -- Timestamps
        to_timestamp(fecha_sys) as created_at,
        to_timestamp(last_fecha_update) as updated_at,
        admin_insert as created_by_admin_id,
        last_admin_update as updated_by_admin_id

    from source
    where codigo is not null
)

select * from renamed
