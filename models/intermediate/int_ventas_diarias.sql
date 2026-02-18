{{
    config(
        materialized='view'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- int_ventas_diarias: enriquece las ventas diarias con:
--   1. Pedidos plataforma (Rappi/PY) = Q registro - pedidos sistema
--   2. Precio y costo estimado para pedidos plataforma (promedio mensual)
--   3. Comisión plataforma (30% del precio de pedidos plataforma)
--   4. Costo delivery (Rapiboy + 20% comisión)
-- ════════════════════════════════════════════════════════════════════════════

with pedidos_sistema as (
    select * from {{ ref('fct_pedidos') }}
    where estado_id = 3  -- Solo entregados
),

-- ── Métricas diarias del sistema ────────────────────────────────────────────
sistema_diario as (
    select
        date_trunc('day', created_at) as fecha,
        count(*) as pedidos_sistema,
        sum(total) as venta_sistema,
        sum(costo_total) as costo_total_sistema,
        sum(kg_total) as kg_sistema,
        round(avg(total), 2) as ticket_promedio_dia,
        round(avg(costo_total), 2) as costo_promedio_dia,
        round(avg(kg_total), 3) as kg_promedio_dia
    from pedidos_sistema
    group by 1
),

-- ── Promedios mensuales (para estimar pedidos plataforma) ───────────────────
promedios_mensuales as (
    select
        strftime(date_trunc('day', created_at), '%Y-%m') as mes,
        round(avg(total), 2) as ticket_promedio_mes,
        round(avg(costo_total), 2) as costo_promedio_mes,
        round(avg(kg_total), 3) as kg_promedio_mes
    from pedidos_sistema
    group by 1
),

-- ── Registro diario (Q real + rapiboy) ──────────────────────────────────────
registro as (
    select * from {{ ref('stg_registro_diario') }}
),

-- ── Cruce: sistema vs registro ──────────────────────────────────────────────
cruce as (
    select
        coalesce(sd.fecha, r.fecha) as fecha,
        r.mes,

        -- Pedidos sistema
        coalesce(sd.pedidos_sistema, 0) as pedidos_sistema,
        coalesce(sd.venta_sistema, 0) as venta_sistema,
        coalesce(sd.costo_total_sistema, 0) as costo_total_sistema,
        coalesce(sd.kg_sistema, 0) as kg_sistema,

        -- Q registro (pedidos reales totales del dia)
        coalesce(r.q_pedidos, coalesce(sd.pedidos_sistema, 0)) as q_pedidos_real,

        -- Pedidos plataforma = Q real - pedidos sistema (mínimo 0)
        greatest(
            coalesce(r.q_pedidos, 0) - coalesce(sd.pedidos_sistema, 0),
            0
        ) as pedidos_plataforma,

        -- Promedios mensuales para estimar plataforma
        coalesce(pm.ticket_promedio_mes, sd.ticket_promedio_dia, 0) as ticket_promedio_mes,
        coalesce(pm.costo_promedio_mes, sd.costo_promedio_dia, 0) as costo_promedio_mes,
        coalesce(pm.kg_promedio_mes, sd.kg_promedio_dia, 0) as kg_promedio_mes,

        -- Delivery (Rapiboy)
        coalesce(r.costo_rapiboy, 0) as costo_rapiboy,
        coalesce(r.costo_delivery_total, 0) as costo_delivery_total

    from sistema_diario sd
    full outer join registro r
        on cast(sd.fecha as date) = r.fecha
    left join promedios_mensuales pm
        on coalesce(r.mes, strftime(sd.fecha, '%Y-%m')) = pm.mes
)

select
    fecha,
    mes,

    -- ── Pedidos sistema ─────────────────────────────────────────────────────
    pedidos_sistema,
    venta_sistema,
    costo_total_sistema,
    kg_sistema,

    -- ── Pedidos plataforma (Rappi/PY) ───────────────────────────────────────
    q_pedidos_real,
    pedidos_plataforma,
    -- Venta estimada plataforma = cant × ticket promedio mensual
    round(pedidos_plataforma * ticket_promedio_mes, 2) as venta_plataforma_estimada,
    -- Costo ingredientes+packaging estimado
    round(pedidos_plataforma * costo_promedio_mes, 2) as costo_plataforma_estimado,
    -- Comisión plataforma (30% del precio de venta)
    round(pedidos_plataforma * ticket_promedio_mes * 0.30, 2) as comision_plataforma,
    -- Kg estimados plataforma
    round(pedidos_plataforma * kg_promedio_mes, 3) as kg_plataforma_estimado,

    -- ── Delivery (Rapiboy) ──────────────────────────────────────────────────
    costo_rapiboy,
    costo_delivery_total,  -- rapiboy + 20% comisión

    -- ── Totales del día ─────────────────────────────────────────────────────
    pedidos_sistema + pedidos_plataforma as pedidos_totales,

    round(
        venta_sistema
        + pedidos_plataforma * ticket_promedio_mes,
    2) as venta_total,

    round(
        costo_total_sistema                                    -- costo sistema
        + pedidos_plataforma * costo_promedio_mes              -- costo plataforma
        + pedidos_plataforma * ticket_promedio_mes * 0.30      -- comisión plataforma 30%
        + costo_delivery_total,                                -- delivery rapiboy +20%
    2) as costo_total,

    round(
        (venta_sistema + pedidos_plataforma * ticket_promedio_mes)
        - (costo_total_sistema
           + pedidos_plataforma * costo_promedio_mes
           + pedidos_plataforma * ticket_promedio_mes * 0.30
           + costo_delivery_total),
    2) as contribucion_mg,

    round(kg_sistema + pedidos_plataforma * kg_promedio_mes, 2) as kg_totales

from cruce
