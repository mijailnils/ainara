{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ ref('costos_sabores') }}
),

sabores as (
    select sabor_id, nombre as sabor_sistema
    from {{ ref('stg_sabores') }}
),

renamed as (
    select
        s.sabor_nombre,
        s.sabor_id,
        sab.sabor_sistema,
        cast(s.mes || '-01' as date) as mes_fecha,
        s.mes,
        extract(year from cast(s.mes || '-01' as date)) as anio,
        extract(month from cast(s.mes || '-01' as date)) as mes_num,
        round(cast(s.costo_por_kg as decimal(10,2)), 2) as costo_por_kg,
        case
            when s.sabor_id is not null then true
            else false
        end as tiene_match

    from source s
    left join sabores sab
        on cast(s.sabor_id as integer) = sab.sabor_id
)

select * from renamed
