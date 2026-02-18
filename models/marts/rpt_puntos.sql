{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_puntos: resumen de puntos de fidelidad por cliente
-- ════════════════════════════════════════════════════════════════════════════

with movimientos as (
    select * from {{ ref('stg_puntos') }}
),

resumen_por_cliente as (
    select
        cliente_id,

        -- Acumulación
        sum(case when tipo_movimiento = 'acumulacion' then puntos_abs else 0 end) as puntos_acumulados,
        count(case when tipo_movimiento = 'acumulacion' then 1 end) as movimientos_acumulacion,

        -- Canje
        sum(case when tipo_movimiento = 'canje' then puntos_abs else 0 end) as puntos_canjeados,
        count(case when tipo_movimiento = 'canje' then 1 end) as movimientos_canje,

        -- Saldos
        sum(case when tipo_movimiento = 'acumulacion' and is_vigente = 1 then puntos_abs else 0 end)
            - sum(case when tipo_movimiento = 'canje' then puntos_abs else 0 end)
        as saldo_vigente,

        sum(case when tipo_movimiento = 'acumulacion' and is_vigente = 0 then puntos_abs else 0 end)
        as saldo_vencido,

        count(*) as total_movimientos,

        -- Fechas
        min(case when tipo_movimiento = 'acumulacion' then fecha end) as fecha_primera_acumulacion,
        max(case when tipo_movimiento = 'acumulacion' then fecha end) as fecha_ultima_acumulacion,
        max(case when tipo_movimiento = 'canje' then fecha end) as fecha_ultimo_canje,

        -- Actividad reciente (últimos 90 días)
        count(case when fecha >= current_date - interval '90 days' then 1 end) > 0 as is_activo_puntos
    from movimientos
    where cliente_id is not null
    group by cliente_id
)

select
    rc.cliente_id,
    dc.nombre,
    dc.segmento_cliente,

    rc.puntos_acumulados,
    rc.puntos_canjeados,
    greatest(rc.saldo_vigente, 0) as saldo_vigente,
    rc.saldo_vencido,

    rc.total_movimientos,
    rc.movimientos_acumulacion,
    rc.movimientos_canje,

    case when rc.puntos_acumulados > 0
        then round(100.0 * rc.puntos_canjeados / rc.puntos_acumulados, 1)
        else 0
    end as ratio_canje,

    rc.fecha_primera_acumulacion,
    rc.fecha_ultima_acumulacion,
    rc.fecha_ultimo_canje,
    rc.is_activo_puntos

from resumen_por_cliente rc
left join {{ ref('dim_clientes') }} dc on rc.cliente_id = dc.cliente_id
order by rc.puntos_acumulados desc
