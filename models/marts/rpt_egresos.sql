{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_egresos: egresos mensuales por categoría con YoY
-- ════════════════════════════════════════════════════════════════════════════

with egresos_mensuales as (
    select
        strftime(cast(fecha as date), '%Y-%m-01')::date as mes,
        extract(year from cast(fecha as date)) as anio,
        extract(month from cast(fecha as date)) as mes_num,
        categoria,
        sum(monto) as monto_total,
        count(*) as cantidad_egresos
    from {{ ref('stg_egresos') }}
    group by 1, 2, 3, 4
),

dolar_mensual as (
    select
        date_trunc('month', fecha)::date as mes,
        round(avg(valor_blue), 2) as tipo_cambio_promedio
    from {{ ref('stg_dolar_blue') }}
    group by 1
),

-- Self-join para YoY
con_yoy as (
    select
        em.mes,
        em.anio,
        em.mes_num,
        em.categoria,
        em.monto_total,
        em.cantidad_egresos,
        prev.monto_total as monto_mismo_mes_anio_anterior,
        case when prev.monto_total > 0
            then round(100.0 * (em.monto_total - prev.monto_total) / prev.monto_total, 1)
            else null
        end as var_interanual_pct
    from egresos_mensuales em
    left join egresos_mensuales prev
        on em.categoria = prev.categoria
        and em.mes_num = prev.mes_num
        and em.anio = prev.anio + 1
)

select
    cy.mes,
    cy.anio,
    cy.mes_num,
    cy.categoria,
    cy.monto_total,
    cy.cantidad_egresos,
    round(cy.monto_total / nullif(dm.tipo_cambio_promedio, 0), 2) as monto_total_usd,
    cy.monto_mismo_mes_anio_anterior,
    cy.var_interanual_pct,
    dm.tipo_cambio_promedio
from con_yoy cy
left join dolar_mensual dm on cy.mes = dm.mes
order by cy.mes desc, cy.monto_total desc
