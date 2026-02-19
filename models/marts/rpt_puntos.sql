{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_puntos: resumen de puntos de fidelidad por identidad
-- ════════════════════════════════════════════════════════════════════════════

with movimientos as (
    select * from {{ ref('stg_puntos') }}
),

-- Mapeo cliente_id → cliente_id_mail_phone via dim_mails
mails as (
    select cliente_id, cliente_id_mail_phone
    from {{ ref('dim_mails') }}
),

resumen_por_identidad as (
    select
        m.cliente_id_mail_phone,

        -- Acumulación
        sum(case when mv.tipo_movimiento = 'acumulacion' then mv.puntos_abs else 0 end) as puntos_acumulados,
        count(case when mv.tipo_movimiento = 'acumulacion' then 1 end) as movimientos_acumulacion,

        -- Canje
        sum(case when mv.tipo_movimiento = 'canje' then mv.puntos_abs else 0 end) as puntos_canjeados,
        count(case when mv.tipo_movimiento = 'canje' then 1 end) as movimientos_canje,

        -- Saldos
        sum(case when mv.tipo_movimiento = 'acumulacion' and mv.is_vigente = 1 then mv.puntos_abs else 0 end)
            - sum(case when mv.tipo_movimiento = 'canje' then mv.puntos_abs else 0 end)
        as saldo_vigente,

        sum(case when mv.tipo_movimiento = 'acumulacion' and mv.is_vigente = 0 then mv.puntos_abs else 0 end)
        as saldo_vencido,

        count(*) as total_movimientos,

        -- Fechas
        min(case when mv.tipo_movimiento = 'acumulacion' then mv.fecha end) as fecha_primera_acumulacion,
        max(case when mv.tipo_movimiento = 'acumulacion' then mv.fecha end) as fecha_ultima_acumulacion,
        max(case when mv.tipo_movimiento = 'canje' then mv.fecha end) as fecha_ultimo_canje,

        -- Actividad reciente (últimos 90 días)
        count(case when mv.fecha >= current_date - interval '90 days' then 1 end) > 0 as is_activo_puntos
    from movimientos mv
    inner join mails m on mv.cliente_id = m.cliente_id
    where mv.cliente_id is not null
      and m.cliente_id_mail_phone is not null
    group by m.cliente_id_mail_phone
)

select
    dc.cliente_id_mail_phone,
    dc.cliente_id,
    dc.nombre,
    dc.segmento_cliente,

    ri.puntos_acumulados,
    ri.puntos_canjeados,
    greatest(ri.saldo_vigente, 0) as saldo_vigente,
    ri.saldo_vencido,

    ri.total_movimientos,
    ri.movimientos_acumulacion,
    ri.movimientos_canje,

    case when ri.puntos_acumulados > 0
        then round(100.0 * ri.puntos_canjeados / ri.puntos_acumulados, 1)
        else 0
    end as ratio_canje,

    ri.fecha_primera_acumulacion,
    ri.fecha_ultima_acumulacion,
    ri.fecha_ultimo_canje,
    ri.is_activo_puntos

from resumen_por_identidad ri
inner join {{ ref('dim_clientes') }} dc on ri.cliente_id_mail_phone = dc.cliente_id_mail_phone
order by ri.puntos_acumulados desc
