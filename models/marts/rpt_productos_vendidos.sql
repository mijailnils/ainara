{{
    config(
        materialized='table'
    )
}}

with productos_pedidos as (
    select
        pp.producto_id,
        pp.pedido_id,
        ped.created_at::date as fecha
    from {{ ref('stg_pedidos_productos') }} pp
    inner join {{ ref('stg_pedidos') }} ped
        on pp.pedido_id = ped.pedido_id
    where ped.is_activo = 1
      and ped.estado_id = 3  -- Entregados
),

productos as (
    select * from {{ ref('stg_productos') }}
),

categorias as (
    select * from {{ ref('stg_productos_categorias') }}
),

-- Costo promedio global por kg (de sabores con match)
costo_global as (
    select round(avg(costo_por_kg), 2) as avg_costo_kg
    from {{ ref('stg_costos_sabores') }}
    where tiene_match = true
),

-- Tipo de cambio promedio del periodo
dolar_promedio as (
    select round(avg(valor_blue), 2) as avg_dolar
    from {{ ref('stg_dolar_blue') }}
),

conteo as (
    select
        producto_id,
        count(*) as veces_vendido,
        count(distinct pedido_id) as pedidos_distintos
    from productos_pedidos
    group by producto_id
)

select
    p.producto_id,
    p.nombre as producto,
    c.nombre as categoria,
    p.precio_base,
    p.peso_kg,
    p.cantidad_gustos,

    coalesce(ct.veces_vendido, 0) as veces_vendido,
    coalesce(ct.pedidos_distintos, 0) as pedidos_distintos,

    -- KG vendidos
    round(coalesce(ct.veces_vendido, 0) * coalesce(p.peso_kg, 0), 2) as kg_vendidos,

    -- Ingreso estimado ARS
    coalesce(ct.veces_vendido, 0) * p.precio_base as ingreso_estimado,

    -- Ingreso estimado USD
    round(coalesce(ct.veces_vendido, 0) * p.precio_base / nullif(dp.avg_dolar, 0), 2) as ingreso_estimado_usd,

    -- Costo estimado (kg * costo promedio global por kg)
    round(coalesce(ct.veces_vendido, 0) * coalesce(p.peso_kg, 0) * cg.avg_costo_kg, 2) as costo_estimado,

    -- Margen estimado ARS
    round(
        coalesce(ct.veces_vendido, 0) * p.precio_base
        - coalesce(ct.veces_vendido, 0) * coalesce(p.peso_kg, 0) * cg.avg_costo_kg,
    2) as margen_estimado,

    -- Margen estimado USD
    round(
        (coalesce(ct.veces_vendido, 0) * p.precio_base
         - coalesce(ct.veces_vendido, 0) * coalesce(p.peso_kg, 0) * cg.avg_costo_kg)
        / nullif(dp.avg_dolar, 0),
    2) as margen_estimado_usd,

    -- Margen %
    case when p.precio_base > 0 then
        round(100.0 * (p.precio_base - coalesce(p.peso_kg, 0) * cg.avg_costo_kg) / p.precio_base, 1)
    end as margen_pct,

    row_number() over (order by coalesce(ct.veces_vendido, 0) desc) as ranking,

    round(100.0 * coalesce(ct.veces_vendido, 0) / nullif(sum(ct.veces_vendido) over (), 0), 2) as porcentaje_del_total

from productos p
left join categorias c on p.categoria_id = c.categoria_id
left join conteo ct on p.producto_id = ct.producto_id
cross join costo_global cg
cross join dolar_promedio dp
where p.is_activo = 1
order by veces_vendido desc
