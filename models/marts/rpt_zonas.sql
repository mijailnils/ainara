{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_zonas: métricas de delivery por zona (clientes por identidad)
-- ════════════════════════════════════════════════════════════════════════════

with mails as (
    select cliente_id, cliente_id_mail_phone
    from {{ ref('dim_mails') }}
),

pedidos_delivery as (
    select
        fp.pedido_id,
        fp.cliente_id,
        m.cliente_id_mail_phone,
        fp.total,
        fp.costo_envio,
        fp.demora_minutos,
        fp.distancia_km,
        fp.total_usd,
        fp.kg_total,
        d.zona_id
    from {{ ref('fct_pedidos') }} fp
    inner join {{ ref('stg_clientes_direcciones') }} d
        on fp.direccion_id = d.direccion_id
    left join mails m on fp.cliente_id = m.cliente_id
    where fp.estado_id = 3
      and fp.tipo_retiro = 'delivery'
      and d.zona_id is not null
),

metricas_por_zona as (
    select
        zona_id,
        count(*) as total_pedidos,
        count(distinct cliente_id_mail_phone) as total_clientes,
        round(sum(total), 2) as venta_total,
        round(avg(total), 2) as ticket_promedio,
        round(sum(costo_envio), 2) as costo_envio_total,
        round(sum(total) - sum(costo_envio), 2) as ingreso_neto,
        round(avg(demora_minutos), 1) as demora_promedio_real,
        round(avg(distancia_km), 2) as distancia_promedio_real,
        round(sum(total_usd), 2) as venta_total_usd,
        round(sum(kg_total), 2) as kg_totales
    from pedidos_delivery
    group by zona_id
),

total_delivery as (
    select sum(total_pedidos) as total from metricas_por_zona
)

select
    mz.zona_id,
    z.distancia_max_km,
    z.precio_envio,
    z.demora_estimada_minutos,

    mz.total_pedidos,
    mz.total_clientes,
    mz.venta_total,
    mz.ticket_promedio,
    mz.costo_envio_total,
    mz.ingreso_neto,
    mz.demora_promedio_real,
    mz.distancia_promedio_real,
    mz.venta_total_usd,
    mz.kg_totales,

    round(100.0 * mz.total_pedidos / td.total, 1) as pct_pedidos_total

from metricas_por_zona mz
inner join {{ ref('stg_zonas') }} z on mz.zona_id = z.zona_id
cross join total_delivery td
order by mz.total_pedidos desc
