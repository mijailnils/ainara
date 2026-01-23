{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('ainara_raw', 'zonas') }}
),

renamed as (
    select
        codigo as zona_id,
        distancia as distancia_max_km,
        precio as precio_envio,
        demora as demora_estimada_minutos,
        activo as is_activo,
        to_timestamp(fecha_sys) as created_at,
        to_timestamp(last_fecha_update) as updated_at,
        admin_insert as created_by_admin_id,
        last_admin_update as updated_by_admin_id

    from source
    where codigo is not null
)

select * from renamed
