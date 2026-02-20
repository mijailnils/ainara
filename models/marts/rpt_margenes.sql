{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_margenes: análisis de márgenes mensual (overall + breakdowns)
-- ════════════════════════════════════════════════════════════════════════════

with pedidos as (
    select * from {{ ref('fct_pedidos') }}
    where estado_id = 3
),

dolar_mensual as (
    select
        date_trunc('month', fecha)::date as mes,
        round(avg(valor_blue), 2) as tipo_cambio_promedio
    from {{ ref('stg_dolar_blue') }}
    group by 1
),

-- Overall mensual
overall as (
    select
        mes,
        extract(year from mes) as anio,
        extract(month from mes) as mes_num,
        'overall' as dimension_tipo,
        'total' as dimension_valor,
        count(*) as pedidos,
        round(sum(total), 2) as venta_total,
        round(sum(costo_total), 2) as costo_total,
        round(sum(contribucion_mg), 2) as contribucion_mg,
        round(sum(kg_total), 2) as kg_totales,
        case when sum(total) > 0
            then round(100.0 * sum(contribucion_mg) / sum(total), 1)
            else 0
        end as margen_pct
    from pedidos
    group by mes
),

-- Por tipo retiro
por_retiro as (
    select
        mes,
        extract(year from mes) as anio,
        extract(month from mes) as mes_num,
        'tipo_retiro' as dimension_tipo,
        tipo_retiro as dimension_valor,
        count(*) as pedidos,
        round(sum(total), 2) as venta_total,
        round(sum(costo_total), 2) as costo_total,
        round(sum(contribucion_mg), 2) as contribucion_mg,
        round(sum(kg_total), 2) as kg_totales,
        case when sum(total) > 0
            then round(100.0 * sum(contribucion_mg) / sum(total), 1)
            else 0
        end as margen_pct
    from pedidos
    group by mes, tipo_retiro
),

-- Por tipo pago
por_pago as (
    select
        mes,
        extract(year from mes) as anio,
        extract(month from mes) as mes_num,
        'tipo_pago' as dimension_tipo,
        tipo_pago as dimension_valor,
        count(*) as pedidos,
        round(sum(total), 2) as venta_total,
        round(sum(costo_total), 2) as costo_total,
        round(sum(contribucion_mg), 2) as contribucion_mg,
        round(sum(kg_total), 2) as kg_totales,
        case when sum(total) > 0
            then round(100.0 * sum(contribucion_mg) / sum(total), 1)
            else 0
        end as margen_pct
    from pedidos
    group by mes, tipo_pago
),

unioned as (
    select * from overall
    union all
    select * from por_retiro
    union all
    select * from por_pago
)

select
    u.mes,
    u.anio,
    u.mes_num,
    u.dimension_tipo,
    u.dimension_valor,
    u.pedidos,
    u.venta_total,
    u.costo_total,
    u.contribucion_mg,
    u.kg_totales,
    u.margen_pct,

    -- USD
    round(u.venta_total / nullif(dm.tipo_cambio_promedio, 0), 2) as venta_total_usd,
    round(u.costo_total / nullif(dm.tipo_cambio_promedio, 0), 2) as costo_total_usd,
    round(u.contribucion_mg / nullif(dm.tipo_cambio_promedio, 0), 2) as contribucion_mg_usd,

    -- Variación vs mes anterior (solo para overall)
    case when u.dimension_tipo = 'overall' then
        u.margen_pct - lag(u.margen_pct) over (
            partition by u.dimension_tipo, u.dimension_valor
            order by u.mes
        )
    end as margen_pct_vs_mes_anterior,

    dm.tipo_cambio_promedio

from unioned u
left join dolar_mensual dm on u.mes::date = dm.mes
order by u.mes desc, u.dimension_tipo, u.dimension_valor
