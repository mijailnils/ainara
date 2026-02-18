{{
    config(
        materialized='view'
    )
}}

with clima as (
    select * from {{ ref('stg_clima') }}
),

-- Quintiles (5 grupos) por temperatura, precipitación y viento
con_quintiles as (
    select
        *,
        ntile(5) over (order by temperatura_maxima) as quintil_temperatura,
        ntile(5) over (order by precipitacion_mm)   as quintil_precipitacion,
        ntile(5) over (order by viento_max_kmh)     as quintil_viento
    from clima
)

select
    fecha,

    -- Temperaturas
    temperatura_maxima,
    temperatura_minima,
    temperatura_promedio,

    -- Clasificación de temperatura (5 grupos)
    quintil_temperatura,
    case quintil_temperatura
        when 1 then 'Muy frio'
        when 2 then 'Frio'
        when 3 then 'Templado'
        when 4 then 'Calido'
        when 5 then 'Muy calido'
    end as categoria_temperatura,

    -- Precipitaciones
    flg_precipitaciones,
    precipitacion_mm,
    lluvia_mm,
    quintil_precipitacion,
    case quintil_precipitacion
        when 1 then 'Sin lluvia'
        when 2 then 'Lluvia leve'
        when 3 then 'Lluvia moderada'
        when 4 then 'Lluvia fuerte'
        when 5 then 'Lluvia intensa'
    end as categoria_precipitacion,

    -- Viento
    viento_max_kmh,
    quintil_viento,
    case quintil_viento
        when 1 then 'Calma'
        when 2 then 'Brisa'
        when 3 then 'Viento moderado'
        when 4 then 'Viento fuerte'
        when 5 then 'Viento muy fuerte'
    end as categoria_viento

from con_quintiles
