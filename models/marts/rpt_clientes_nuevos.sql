{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_clientes_nuevos: adquisición mensual de clientes y retención
-- ════════════════════════════════════════════════════════════════════════════

with primer_pedido as (
    select
        identidad,
        fecha_primer_pedido,
        pedido_id
    from {{ ref('int_primer_pedido') }}
    where is_primer_pedido = true
),

-- Mes de adquisición por identidad
cohort as (
    select
        identidad,
        date_trunc('month', fecha_primer_pedido)::date as mes_adquisicion,
        fecha_primer_pedido,
        pedido_id as primer_pedido_id
    from primer_pedido
),

-- Info del primer pedido
primer_info as (
    select
        co.identidad,
        co.mes_adquisicion,
        fp.tipo_retiro,
        fp.tipo_pago,
        fp.total as ticket_primer_pedido
    from cohort co
    inner join {{ ref('fct_pedidos') }} fp on co.primer_pedido_id = fp.pedido_id
),

-- Pedidos subsiguientes (para retención)
todos_pedidos as (
    select
        pp.identidad,
        pp.fecha_primer_pedido,
        fp.created_at as fecha_pedido
    from primer_pedido pp
    inner join {{ ref('int_primer_pedido') }} ip
        on pp.identidad = ip.identidad
    inner join {{ ref('fct_pedidos') }} fp
        on ip.pedido_id = fp.pedido_id
    where fp.estado_id = 3
      and ip.is_primer_pedido = false
),

retencion as (
    select
        co.identidad,
        co.mes_adquisicion,
        max(case when tp.fecha_pedido <= co.fecha_primer_pedido + interval '30 days' then 1 else 0 end) as retuvo_30d,
        max(case when tp.fecha_pedido <= co.fecha_primer_pedido + interval '60 days' then 1 else 0 end) as retuvo_60d,
        max(case when tp.fecha_pedido <= co.fecha_primer_pedido + interval '90 days' then 1 else 0 end) as retuvo_90d
    from cohort co
    left join todos_pedidos tp on co.identidad = tp.identidad
    group by co.identidad, co.mes_adquisicion
),

-- Agregación mensual
nuevos_por_mes as (
    select
        pi.mes_adquisicion as mes,
        extract(year from pi.mes_adquisicion) as anio,
        extract(month from pi.mes_adquisicion) as mes_num,

        count(distinct pi.identidad) as clientes_nuevos,

        -- Canal primer pedido
        count(case when pi.tipo_retiro = 'delivery' then 1 end) as nuevos_delivery,
        count(case when pi.tipo_retiro = 'local' then 1 end) as nuevos_local,
        count(case when pi.tipo_retiro = 'mostrador' then 1 end) as nuevos_mostrador,

        count(case when pi.tipo_pago = 'cash' then 1 end) as nuevos_efectivo,
        count(case when pi.tipo_pago = 'mp' then 1 end) as nuevos_mp,
        count(case when pi.tipo_pago = 'transfer' then 1 end) as nuevos_transferencia,

        round(avg(pi.ticket_primer_pedido), 2) as ticket_promedio_primer_pedido
    from primer_info pi
    group by pi.mes_adquisicion
),

retencion_mensual as (
    select
        mes_adquisicion as mes,
        round(100.0 * sum(retuvo_30d) / count(*), 1) as retencion_30d_pct,
        round(100.0 * sum(retuvo_60d) / count(*), 1) as retencion_60d_pct,
        round(100.0 * sum(retuvo_90d) / count(*), 1) as retencion_90d_pct
    from retencion
    group by mes_adquisicion
)

select
    nm.mes,
    nm.anio,
    nm.mes_num,

    -- Estación / Temporada
    case
        when nm.mes_num in (12, 1, 2) then 'Verano'
        when nm.mes_num in (3, 4, 5)  then 'Otoño'
        when nm.mes_num in (6, 7, 8)  then 'Invierno'
        when nm.mes_num in (9, 10, 11) then 'Primavera'
    end as estacion,
    case
        when nm.mes_num in (11, 12, 1, 2) then 'Alta'
        when nm.mes_num in (4, 5, 6, 7, 8) then 'Baja'
        else 'Media'
    end as temporada,

    nm.clientes_nuevos,
    nm.nuevos_delivery,
    nm.nuevos_local,
    nm.nuevos_mostrador,
    nm.nuevos_efectivo,
    nm.nuevos_mp,
    nm.nuevos_transferencia,
    nm.ticket_promedio_primer_pedido,

    -- Retención
    rm.retencion_30d_pct,
    rm.retencion_60d_pct,
    rm.retencion_90d_pct,

    -- Mes anterior
    lag(nm.clientes_nuevos) over (order by nm.mes) as clientes_nuevos_mes_anterior,
    case when lag(nm.clientes_nuevos) over (order by nm.mes) > 0
        then round(100.0 * (nm.clientes_nuevos - lag(nm.clientes_nuevos) over (order by nm.mes))
            / lag(nm.clientes_nuevos) over (order by nm.mes), 1)
        else null
    end as var_vs_mes_anterior_pct

from nuevos_por_mes nm
left join retencion_mensual rm on nm.mes = rm.mes
order by nm.mes desc
