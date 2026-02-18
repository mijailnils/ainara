{{
    config(
        materialized='view'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- int_costos_pedido: calcula el costo de ingredientes + packaging por pedido
-- ════════════════════════════════════════════════════════════════════════════

with pedidos_fecha as (
    select
        pedido_id,
        date_trunc('day', created_at) as fecha,
        strftime(created_at, '%Y-%m') as mes
    from {{ ref('stg_pedidos') }}
),

-- ── Cada sabor dentro de cada producto de cada pedido ───────────────────────
lineas_sabor as (
    select
        pp.pedido_id,
        pp.pedido_producto_id,
        pp.producto_id,
        pps.sabor_id,
        pr.peso_kg,
        pr.nombre as producto_nombre,
        -- Contar cuántos sabores tiene este producto en este pedido
        count(*) over (partition by pp.pedido_producto_id) as sabores_en_producto
    from {{ ref('stg_pedidos_productos') }} pp
    inner join {{ ref('stg_productos') }} pr
        on pp.producto_id = pr.producto_id
    inner join {{ ref('stg_pedidos_productos_sabores') }} pps
        on pp.pedido_producto_id = pps.pedido_producto_id
    where pr.peso_kg > 0
),

-- ── Costo promedio por kg por mes (para fallback y escalar packaging) ────────
indice_costos as (
    select
        mes,
        avg(costo_por_kg) as avg_costo_kg
    from {{ ref('stg_costos_sabores') }}
    where tiene_match = true
    group by mes
),

-- ── Peso por sabor y cruce con costos ───────────────────────────────────────
lineas_con_costo as (
    select
        ls.pedido_id,
        ls.pedido_producto_id,
        ls.producto_id,
        ls.sabor_id,
        ls.producto_nombre,
        ls.peso_kg,
        ls.sabores_en_producto,
        pf.fecha,
        pf.mes,
        -- kg que corresponde a este sabor
        ls.peso_kg / nullif(ls.sabores_en_producto, 0) as kg_por_sabor,
        cs.costo_por_kg,
        -- Fallback: si no hay costo del sabor, usar promedio del mes
        coalesce(cs.costo_por_kg, ic.avg_costo_kg) as costo_por_kg_usado,
        case when cs.costo_por_kg is not null then 'exacto' else 'promedio' end as tipo_costo,
        -- Costo de este sabor = kg × costo/kg (con fallback a promedio)
        (ls.peso_kg / nullif(ls.sabores_en_producto, 0))
            * coalesce(cs.costo_por_kg, ic.avg_costo_kg, 0) as costo_sabor
    from lineas_sabor ls
    inner join pedidos_fecha pf
        on ls.pedido_id = pf.pedido_id
    left join {{ ref('stg_costos_sabores') }} cs
        on ls.sabor_id = cs.sabor_id
        and pf.mes = cs.mes
    left join indice_costos ic
        on pf.mes = ic.mes
),

-- ── Costo de ingredientes por pedido ────────────────────────────────────────
costo_ingredientes as (
    select
        pedido_id,
        round(sum(costo_sabor), 2) as costo_ingredientes,
        count(*) as total_lineas_sabor,
        sum(case when tipo_costo = 'exacto' then 1 else 0 end) as sabores_con_costo,
        sum(case when tipo_costo = 'promedio' then 1 else 0 end) as sabores_con_promedio
    from lineas_con_costo
    group by pedido_id
),

ultimo_mes as (
    select max(mes) as mes_ref, max(avg_costo_kg) as avg_ref
    from indice_costos
    where mes = (select max(mes) from indice_costos)
),

indice_normalizado as (
    select
        ic.mes,
        ic.avg_costo_kg / um.avg_ref as factor
    from indice_costos ic
    cross join ultimo_mes um
),

-- ── Packaging por pedido ────────────────────────────────────────────────────
-- Potes de telgopor: solo productos en pote (excluir cucurucho/vasito/capelina)
-- Costo base actual (último mes): cuarto=250, medio=350, 3/4=450, kilo=550
-- Bolsa: 1 por pedido, costo base actual=100
productos_pedido as (
    select
        pp.pedido_id,
        pf.mes,
        pr.peso_kg,
        pr.nombre as producto_nombre,
        -- Flag: necesita pote de telgopor?
        case
            when lower(pr.nombre) like '%cucuruch%' then false
            when lower(pr.nombre) like '%vasito%'   then false
            when lower(pr.nombre) like '%capelina%' then false
            when pr.peso_kg > 0                     then true
            else false
        end as necesita_pote,
        -- Costo del pote según tamaño (precios actuales)
        case
            when lower(pr.nombre) like '%cucuruch%' then 0
            when lower(pr.nombre) like '%vasito%'   then 0
            when lower(pr.nombre) like '%capelina%' then 0
            when pr.peso_kg <= 0.25                 then 250
            when pr.peso_kg <= 0.5                  then 350
            when pr.peso_kg <= 0.75                 then 450
            when pr.peso_kg <= 1.0                  then 550
            when pr.peso_kg <= 1.5                  then 750
            when pr.peso_kg <= 2.0                  then 950
            else 550
        end as costo_pote_actual
    from {{ ref('stg_pedidos_productos') }} pp
    inner join {{ ref('stg_productos') }} pr
        on pp.producto_id = pr.producto_id
    inner join pedidos_fecha pf
        on pp.pedido_id = pf.pedido_id
    where pr.peso_kg > 0
),

costo_packaging as (
    select
        ppd.pedido_id,
        ppd.mes,
        -- Potes: costo actual × factor de inflación del mes
        round(sum(ppd.costo_pote_actual * coalesce(idx.factor, 1)), 2)
            as costo_potes,
        -- Bolsa: 1 por pedido
        round(100 * coalesce(min(idx.factor), 1), 2)
            as costo_bolsa
    from productos_pedido ppd
    left join indice_normalizado idx
        on ppd.mes = idx.mes
    group by ppd.pedido_id, ppd.mes
)

-- ── Resultado final ─────────────────────────────────────────────────────────
select
    pf.pedido_id,
    pf.fecha,
    pf.mes,

    -- Costos
    coalesce(ci.costo_ingredientes, 0) as costo_ingredientes,
    coalesce(cp.costo_potes, 0) as costo_potes,
    coalesce(cp.costo_bolsa, 0) as costo_bolsa,
    coalesce(ci.costo_ingredientes, 0)
        + coalesce(cp.costo_potes, 0)
        + coalesce(cp.costo_bolsa, 0) as costo_total,

    -- Cobertura de costeo
    coalesce(ci.total_lineas_sabor, 0) as total_lineas_sabor,
    coalesce(ci.sabores_con_costo, 0) as sabores_con_costo,
    coalesce(ci.sabores_con_promedio, 0) as sabores_con_promedio

from pedidos_fecha pf
left join costo_ingredientes ci
    on pf.pedido_id = ci.pedido_id
left join costo_packaging cp
    on pf.pedido_id = cp.pedido_id
