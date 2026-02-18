{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_sabores: ranking de sabores con kg, ingreso, margen y estacionalidad
-- Reemplaza rpt_sabores_populares
-- ════════════════════════════════════════════════════════════════════════════

with pedidos_entregados as (
    select pedido_id, created_at
    from {{ ref('stg_pedidos') }}
    where estado_id = 3
),

-- Cada línea sabor con su peso
lineas_sabor as (
    select
        pps.sabor_id,
        pp.pedido_id,
        pp.producto_id,
        pr.peso_kg,
        pr.nombre as producto_nombre,
        pr.precio_base,
        pe.created_at,
        -- kg por sabor = peso / cantidad de sabores en el producto
        pr.peso_kg / nullif(
            count(*) over (partition by pp.pedido_producto_id), 0
        ) as kg_por_sabor,
        -- Estación del pedido
        case
            when month(pe.created_at) in (12, 1, 2) then 'Verano'
            when month(pe.created_at) in (3, 4, 5)  then 'Otoño'
            when month(pe.created_at) in (6, 7, 8)  then 'Invierno'
            when month(pe.created_at) in (9, 10, 11) then 'Primavera'
        end as estacion
    from {{ ref('stg_pedidos_productos_sabores') }} pps
    inner join {{ ref('stg_pedidos_productos') }} pp
        on pps.pedido_producto_id = pp.pedido_producto_id
    inner join {{ ref('stg_productos') }} pr
        on pp.producto_id = pr.producto_id
    inner join pedidos_entregados pe
        on pp.pedido_id = pe.pedido_id
    where pr.peso_kg > 0
),

-- Costo promedio global por sabor
costo_promedio as (
    select
        sabor_id,
        round(avg(costo_por_kg), 2) as costo_promedio_kg
    from {{ ref('stg_costos_sabores') }}
    where tiene_match = true
    group by sabor_id
),

-- Métricas por sabor
metricas as (
    select
        ls.sabor_id,
        count(*) as veces_pedido,
        count(distinct ls.pedido_id) as pedidos_distintos,
        round(sum(ls.kg_por_sabor), 2) as kg_vendidos,

        -- Estacionalidad
        count(case when ls.estacion = 'Verano' then 1 end) as n_verano,
        count(case when ls.estacion = 'Otoño' then 1 end) as n_otono,
        count(case when ls.estacion = 'Invierno' then 1 end) as n_invierno,
        count(case when ls.estacion = 'Primavera' then 1 end) as n_primavera
    from lineas_sabor ls
    group by ls.sabor_id
),

total_pedidos as (
    select sum(veces_pedido) as total from metricas
)

select
    m.sabor_id,
    s.nombre as sabor,
    sc.nombre as categoria,
    s.is_sin_azucar,

    m.veces_pedido,
    m.pedidos_distintos,
    m.kg_vendidos,

    -- Ingreso estimado (kg × precio promedio por kg del sistema)
    round(m.kg_vendidos * coalesce(cp.costo_promedio_kg, 0) * 3, 2) as ingreso_estimado,
    coalesce(cp.costo_promedio_kg, 0) as costo_promedio_kg,
    round(coalesce(cp.costo_promedio_kg, 0) * 3 - coalesce(cp.costo_promedio_kg, 0), 2) as margen_estimado_por_kg,

    -- Ranking
    row_number() over (order by m.veces_pedido desc) as ranking,
    round(100.0 * m.veces_pedido / tp.total, 2) as porcentaje_del_total,

    -- Estacionalidad
    case greatest(m.n_verano, m.n_otono, m.n_invierno, m.n_primavera)
        when m.n_verano then 'Verano'
        when m.n_otono then 'Otoño'
        when m.n_invierno then 'Invierno'
        when m.n_primavera then 'Primavera'
    end as estacion_top,
    round(100.0 * m.n_verano / m.veces_pedido, 1) as pct_verano,
    round(100.0 * m.n_otono / m.veces_pedido, 1) as pct_otono,
    round(100.0 * m.n_invierno / m.veces_pedido, 1) as pct_invierno,
    round(100.0 * m.n_primavera / m.veces_pedido, 1) as pct_primavera

from metricas m
inner join {{ ref('stg_sabores') }} s on m.sabor_id = s.sabor_id
left join {{ ref('stg_sabores_categorias') }} sc on s.categoria_id = sc.categoria_id
left join costo_promedio cp on m.sabor_id = cp.sabor_id
cross join total_pedidos tp
order by m.veces_pedido desc
