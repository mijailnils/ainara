{{
    config(
        materialized='view'
    )
}}

with puntos as (
    select * from {{ ref('puntos') }}
),

-- Mapeo de cliente_id del sistema de puntos → cliente_id del sistema principal
points_clientes as (
    select
        id as points_cliente_id,
        remote_id as cliente_id,
        nombre as points_nombre,
        email as points_email
    from {{ ref('points_clientes') }}
),

renamed as (
    select
        p.id as punto_id,
        pc.cliente_id,
        p.cliente_id as points_cliente_id,
        p.puntos,
        case
            when p.puntos > 0 then 'acumulacion'
            when p.puntos < 0 then 'canje'
            else 'sin_movimiento'
        end as tipo_movimiento,
        abs(p.puntos) as puntos_abs,
        cast(p.fecha as timestamp) as fecha,
        cast(p.vencimiento as date) as vencimiento,
        case
            when cast(p.vencimiento as date) >= current_date then 1
            else 0
        end as is_vigente

    from puntos p
    left join points_clientes pc
        on p.cliente_id = pc.points_cliente_id
)

select * from renamed
