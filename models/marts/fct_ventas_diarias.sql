{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- fct_ventas_diarias: resumen diario completo
-- Fuente principal: int_ventas_diarias (incluye sistema + plataforma)
-- Enrichments: clima, USD, detalles de sistema por tipo retiro/pago
-- ════════════════════════════════════════════════════════════════════════════

with ventas_base as (
    select * from {{ ref('int_ventas_diarias') }}
),

clima as (
    select * from {{ ref('int_clima') }}
),

dolar as (
    select * from {{ ref('stg_dolar_blue') }}
),

-- Detalles del sistema (breakdowns que solo vienen de fct_pedidos)
sistema_detalle as (
    select
        fecha,
        count(distinct cliente_id) as clientes_unicos,
        round(avg(total), 2) as ticket_promedio,

        -- Por tipo de retiro
        count(case when tipo_retiro = 'delivery' then 1 end) as pedidos_delivery,
        count(case when tipo_retiro = 'local' then 1 end) as pedidos_local,
        count(case when tipo_retiro = 'mostrador' then 1 end) as pedidos_mostrador,

        -- Por tipo de pago
        count(case when tipo_pago = 'cash' then 1 end) as pagos_efectivo,
        count(case when tipo_pago = 'mp' then 1 end) as pagos_mercadopago,
        count(case when tipo_pago = 'transfer' then 1 end) as pagos_transferencia,

        -- Ventas por tipo de pago
        sum(case when tipo_pago = 'cash' then total else 0 end) as venta_efectivo,
        sum(case when tipo_pago = 'mp' then total else 0 end) as venta_mercadopago,
        sum(case when tipo_pago = 'transfer' then total else 0 end) as venta_transferencia,

        -- MercadoPago
        sum(mp_comision) as comision_mp_total,
        sum(mp_monto_neto_recibido) as neto_mp_total,

        -- Productos y sabores
        sum(cantidad_productos) as productos_vendidos,
        sum(cantidad_sabores) as sabores_vendidos,

        -- Primer pedido
        count(case when is_primer_pedido then 1 end) as pedidos_primer_pedido
    from {{ ref('fct_pedidos') }}
    where estado_id = 3
    group by fecha
)

select
    vb.fecha,
    date_trunc('week', vb.fecha) as semana,
    vb.mes,
    extract(year from vb.fecha) as anio,
    extract(month from vb.fecha) as mes_num,
    dayofweek(vb.fecha) as dia_semana,

    -- Estación argentina
    case
        when extract(month from vb.fecha) in (12, 1, 2) then 'Verano'
        when extract(month from vb.fecha) in (3, 4, 5)  then 'Otoño'
        when extract(month from vb.fecha) in (6, 7, 8)  then 'Invierno'
        when extract(month from vb.fecha) in (9, 10, 11) then 'Primavera'
    end as estacion,
    case
        when extract(month from vb.fecha) in (11, 12, 1) then 'Alta'
        when extract(month from vb.fecha) in (5, 6, 7) then 'Baja'
        else 'Media'
    end as temporada,

    -- Clima
    cl.temperatura_maxima,
    cl.temperatura_minima,
    cl.temperatura_promedio,
    cl.categoria_temperatura,
    cl.flg_precipitaciones,
    cl.precipitacion_mm,
    cl.categoria_precipitacion,
    cl.viento_max_kmh,
    cl.categoria_viento,

    -- ── Pedidos ────────────────────────────────────────────────────────────
    vb.pedidos_sistema,
    vb.pedidos_plataforma,
    vb.pedidos_totales,
    vb.q_pedidos_real,

    -- ── Ventas ARS ─────────────────────────────────────────────────────────
    vb.venta_sistema,
    vb.venta_plataforma_estimada,
    vb.venta_total,

    -- ── Costos ─────────────────────────────────────────────────────────────
    vb.costo_total_sistema,
    vb.costo_plataforma_estimado,
    vb.comision_plataforma,
    vb.costo_rapiboy,
    vb.costo_delivery_total,
    vb.costo_total,

    -- ── Margen ─────────────────────────────────────────────────────────────
    vb.contribucion_mg,
    case when vb.venta_total > 0
        then round(100.0 * vb.contribucion_mg / vb.venta_total, 1)
        else 0
    end as margen_pct,

    -- ── KG ─────────────────────────────────────────────────────────────────
    vb.kg_sistema,
    vb.kg_plataforma_estimado,
    vb.kg_totales,

    -- ── USD ────────────────────────────────────────────────────────────────
    db.valor_blue as tipo_cambio_blue,
    round(vb.venta_total / nullif(db.valor_blue, 0), 2) as venta_total_usd,
    round(vb.costo_total / nullif(db.valor_blue, 0), 2) as costo_total_usd,
    round(vb.contribucion_mg / nullif(db.valor_blue, 0), 2) as contribucion_mg_usd,

    -- ── Detalle sistema (tipo retiro/pago) ─────────────────────────────────
    coalesce(sd.clientes_unicos, 0) as clientes_unicos,
    coalesce(sd.ticket_promedio, 0) as ticket_promedio,

    coalesce(sd.pedidos_delivery, 0) as pedidos_delivery,
    coalesce(sd.pedidos_local, 0) as pedidos_local,
    coalesce(sd.pedidos_mostrador, 0) as pedidos_mostrador,

    coalesce(sd.pagos_efectivo, 0) as pagos_efectivo,
    coalesce(sd.pagos_mercadopago, 0) as pagos_mercadopago,
    coalesce(sd.pagos_transferencia, 0) as pagos_transferencia,

    coalesce(sd.venta_efectivo, 0) as venta_efectivo,
    coalesce(sd.venta_mercadopago, 0) as venta_mercadopago,
    coalesce(sd.venta_transferencia, 0) as venta_transferencia,

    coalesce(sd.comision_mp_total, 0) as comision_mp_total,
    coalesce(sd.neto_mp_total, 0) as neto_mp_total,

    coalesce(sd.productos_vendidos, 0) as productos_vendidos,
    coalesce(sd.sabores_vendidos, 0) as sabores_vendidos,
    coalesce(sd.pedidos_primer_pedido, 0) as pedidos_primer_pedido

from ventas_base vb
left join clima cl on cast(vb.fecha as date) = cl.fecha
left join dolar db on cast(vb.fecha as date) = db.fecha
left join sistema_detalle sd on vb.fecha = sd.fecha
order by vb.fecha desc
