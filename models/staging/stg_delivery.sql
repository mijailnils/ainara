{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('ainara_raw', 'delivery') }}
),

renamed as (
    select
        codigo as delivery_id,
        pedidos as pedidos_ids,  -- Viene como string con IDs separados
        repartidor,
        total,
        estado as estado_id,
        activo as is_activo,
        to_timestamp(fecha_sys) as created_at,
        to_timestamp(last_fecha_update) as updated_at,
        admin_insert as created_by_admin_id,
        last_admin_update as updated_by_admin_id

    from source
    where codigo is not null
)

select * from renamed
