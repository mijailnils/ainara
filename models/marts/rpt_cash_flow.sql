{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_cash_flow: flujo de caja mensual
-- Inflows (cobros por medio de pago) vs Outflows (egresos + delivery)
-- ════════════════════════════════════════════════════════════════════════════

with inflows as (
    select
        date_trunc('month', fecha)::date as mes,
        extract(year from fecha) as anio,
        extract(month from fecha) as mes_num,

        sum(venta_efectivo) as cobros_efectivo,
        sum(neto_mp_total) as cobros_mp_neto,
        sum(venta_transferencia) as cobros_transferencia,
        sum(venta_efectivo) + sum(neto_mp_total) + sum(venta_transferencia) as total_inflows
    from {{ ref('fct_ventas_diarias') }}
    group by 1, 2, 3
),

outflows as (
    select
        strftime(cast(fecha as date), '%Y-%m-01')::date as mes,
        sum(case when medio_pago = 'efectivo' then monto else 0 end) as egresos_efectivo,
        sum(case when medio_pago = 'tarjeta_credito' then monto else 0 end) as egresos_tarjeta,
        sum(case when medio_pago = 'mercadopago' then monto else 0 end) as egresos_mp,
        sum(case when medio_pago = 'otro' then monto else 0 end) as egresos_otro,
        sum(monto) as total_egresos
    from {{ ref('stg_egresos') }}
    group by 1
),

delivery as (
    select
        date_trunc('month', fecha)::date as mes,
        sum(costo_delivery_total) as costo_delivery
    from {{ ref('fct_ventas_diarias') }}
    group by 1
),

dolar_mensual as (
    select
        date_trunc('month', fecha)::date as mes,
        round(avg(valor_blue), 2) as tipo_cambio_promedio
    from {{ ref('stg_dolar_blue') }}
    group by 1
),

cashflow as (
    select
        i.mes,
        i.anio,
        i.mes_num,

        -- Inflows
        i.cobros_efectivo,
        i.cobros_mp_neto,
        i.cobros_transferencia,
        i.total_inflows,

        -- Outflows
        coalesce(o.egresos_efectivo, 0) as egresos_efectivo,
        coalesce(o.egresos_tarjeta, 0) as egresos_tarjeta,
        coalesce(o.egresos_mp, 0) as egresos_mp,
        coalesce(o.egresos_otro, 0) as egresos_otro,
        coalesce(dl.costo_delivery, 0) as costo_delivery,
        coalesce(o.total_egresos, 0) + coalesce(dl.costo_delivery, 0) as total_outflows,

        -- Net
        i.total_inflows - coalesce(o.total_egresos, 0) - coalesce(dl.costo_delivery, 0) as flujo_neto,

        -- USD
        dm.tipo_cambio_promedio
    from inflows i
    left join outflows o on i.mes = o.mes
    left join delivery dl on i.mes = dl.mes
    left join dolar_mensual dm on i.mes = dm.mes
)

select
    *,
    sum(flujo_neto) over (order by mes rows unbounded preceding) as flujo_neto_acumulado,
    round(total_inflows / nullif(tipo_cambio_promedio, 0), 2) as total_inflows_usd,
    round(total_outflows / nullif(tipo_cambio_promedio, 0), 2) as total_outflows_usd,
    round(flujo_neto / nullif(tipo_cambio_promedio, 0), 2) as flujo_neto_usd
from cashflow
order by mes desc
