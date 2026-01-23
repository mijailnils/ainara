{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('ainara_raw', 'clientes_direcciones') }}
),

renamed as (
    select
        codigo as direccion_id,
        cliente as cliente_id,
        direccion,
        piso,
        depto,
        barrio,
        map_lat as latitud,
        map_lng as longitud,
        distancia as distancia_km,
        zona as zona_id,
        observaciones,
        activo as is_activo,
        to_timestamp(fecha_sys) as created_at,
        to_timestamp(last_fecha_update) as updated_at,
        admin_insert as created_by_admin_id,
        last_admin_update as updated_by_admin_id

    from source
    where codigo is not null
)

select * from renamed
