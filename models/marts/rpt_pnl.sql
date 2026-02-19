{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_pnl: Estado de Resultados mensual
-- Ingresos → COGS → Margen bruto → Gastos Op → Comisiones → Resultado
-- ════════════════════════════════════════════════════════════════════════════

with ingresos_mensuales as (
    select
        date_trunc('month', fecha)::date as mes,
        extract(year from fecha) as anio,
        extract(month from fecha) as mes_num,

        sum(venta_sistema) as venta_sistema,
        sum(venta_plataforma_estimada) as venta_plataforma,
        sum(venta_total) as ingresos_totales,

        -- COGS
        sum(costo_total_sistema) as cogs_sistema,
        sum(costo_plataforma_estimado) as cogs_plataforma,
        sum(costo_total_sistema) + sum(costo_plataforma_estimado) as cogs_total,

        -- Comisiones
        sum(comision_mp_total) as comision_mp,
        sum(comision_plataforma) as comision_plataforma,
        sum(comision_mp_total) + sum(comision_plataforma) as total_comisiones,

        -- Delivery
        sum(costo_delivery_total) as costo_delivery,

        -- Métricas operativas
        sum(pedidos_totales) as pedidos_totales,
        sum(kg_totales) as kg_totales
    from {{ ref('fct_ventas_diarias') }}
    group by 1, 2, 3
),

egresos_mensuales as (
    select
        strftime(cast(fecha as date), '%Y-%m-01')::date as mes,
        sum(case when categoria = 'Mano de obra' then monto else 0 end) as gasto_mano_obra,
        sum(case when categoria = 'Alquiler' then monto else 0 end) as gasto_alquiler,
        sum(case when categoria = 'Servicios' then monto else 0 end) as gasto_servicios,
        sum(case when categoria = 'Marketing' then monto else 0 end) as gasto_marketing,
        sum(case when categoria = 'Impuestos' then monto else 0 end) as gasto_impuestos,
        sum(case when categoria = 'Logistica' then monto else 0 end) as gasto_logistica,
        sum(case when categoria not in (
            'Mano de obra','Alquiler','Servicios','Marketing','Impuestos','Logistica',
            'Insumos','Potes'  -- excluidos: ya están en COGS por pedido
        ) then monto else 0 end) as gasto_otros,
        sum(case when categoria not in ('Insumos','Potes')
            then monto else 0 end) as total_gastos_operativos
    from {{ ref('stg_egresos') }}
    group by 1
),

dolar_mensual as (
    select
        date_trunc('month', fecha)::date as mes,
        round(avg(valor_blue), 2) as tipo_cambio_promedio
    from {{ ref('stg_dolar_blue') }}
    group by 1
)

select
    im.mes,
    im.anio,
    im.mes_num,

    -- Ingresos
    im.venta_sistema,
    im.venta_plataforma,
    im.ingresos_totales,

    -- COGS
    im.cogs_sistema,
    im.cogs_plataforma,
    im.cogs_total,

    -- Margen bruto
    im.ingresos_totales - im.cogs_total as margen_bruto,
    case when im.ingresos_totales > 0
        then round(100.0 * (im.ingresos_totales - im.cogs_total) / im.ingresos_totales, 1)
        else 0
    end as margen_bruto_pct,

    -- Gastos operativos
    coalesce(em.gasto_mano_obra, 0) as gasto_mano_obra,
    coalesce(em.gasto_alquiler, 0) as gasto_alquiler,
    coalesce(em.gasto_servicios, 0) as gasto_servicios,
    coalesce(em.gasto_marketing, 0) as gasto_marketing,
    coalesce(em.gasto_impuestos, 0) as gasto_impuestos,
    coalesce(em.gasto_logistica, 0) as gasto_logistica,
    coalesce(em.gasto_otros, 0) as gasto_otros,
    coalesce(em.total_gastos_operativos, 0) as total_gastos_operativos,

    -- Comisiones
    im.comision_mp,
    im.comision_plataforma,
    im.total_comisiones,

    -- Delivery
    im.costo_delivery,

    -- Resultado operativo
    im.ingresos_totales
        - im.cogs_total
        - coalesce(em.total_gastos_operativos, 0)
        - im.total_comisiones
        - im.costo_delivery
    as resultado_operativo,

    case when im.ingresos_totales > 0
        then round(100.0 * (
            im.ingresos_totales
            - im.cogs_total
            - coalesce(em.total_gastos_operativos, 0)
            - im.total_comisiones
            - im.costo_delivery
        ) / im.ingresos_totales, 1)
        else 0
    end as resultado_operativo_pct,

    -- USD
    dm.tipo_cambio_promedio,
    round(im.ingresos_totales / nullif(dm.tipo_cambio_promedio, 0), 2) as ingresos_totales_usd,
    round(im.cogs_total / nullif(dm.tipo_cambio_promedio, 0), 2) as cogs_total_usd,
    round((im.ingresos_totales - im.cogs_total) / nullif(dm.tipo_cambio_promedio, 0), 2) as margen_bruto_usd,
    round(coalesce(em.total_gastos_operativos, 0) / nullif(dm.tipo_cambio_promedio, 0), 2) as total_gastos_operativos_usd,
    round((im.ingresos_totales - im.cogs_total - coalesce(em.total_gastos_operativos, 0)
        - im.total_comisiones - im.costo_delivery) / nullif(dm.tipo_cambio_promedio, 0), 2) as resultado_operativo_usd,

    -- Métricas operativas
    im.pedidos_totales,
    im.kg_totales

from ingresos_mensuales im
left join egresos_mensuales em on im.mes = em.mes
left join dolar_mensual dm on im.mes = dm.mes
order by im.mes desc
