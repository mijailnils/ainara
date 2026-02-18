{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ ref('clima_buenos_aires') }}
),

renamed as (
    select
        cast(fecha as date) as fecha,

        -- Temperaturas
        temp_max_c as temperatura_maxima,
        temp_min_c as temperatura_minima,
        round((temp_max_c + temp_min_c) / 2, 1) as temperatura_promedio,

        -- Flag de precipitaciones (1 si llovió, 0 si no)
        case when precipitacion_mm > 0 then 1 else 0 end as flg_precipitaciones,

        -- Datos completos de precipitación y viento
        precipitacion_mm,
        lluvia_mm,
        viento_max_kmh

    from source
)

select * from renamed
