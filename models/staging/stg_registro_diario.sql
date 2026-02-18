{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ ref('registro_diario_ventas') }}
),

renamed as (
    select
        cast(fecha as date) as fecha,
        dia_nombre,
        q_pedidos,
        total_rapiboys as costo_rapiboy,
        -- Rapiboy cobra 20% de comisión sobre el monto
        round(total_rapiboys * 1.20, 2) as costo_delivery_total,
        extract(year from cast(fecha as date)) as anio,
        extract(month from cast(fecha as date)) as mes_num,
        strftime(cast(fecha as date), '%Y-%m') as mes

    from source
    where fecha is not null
)

select * from renamed
