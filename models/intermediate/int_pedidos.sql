{{
    config(
        materialized='view'
    )
}}

with pedidos as (
    select * from {{ ref('fct_pedidos') }}
),

clima as (
    select * from {{ ref('int_clima') }}
),

-- Un registro por cliente (el más reciente) con cliente_id_mail_phone y ultimo_barrio
clientes_dedup as (
    select distinct on (cliente_id)
        cliente_id,
        cliente_id_mail_phone,
        ultimo_barrio
    from {{ ref('int_clientes') }}
    order by cliente_id, created_at desc
),

-- Segmento via dim_mails → dim_clientes (dim_clientes es 1 fila por identidad)
segmentos as (
    select m.cliente_id, dc.segmento_cliente
    from {{ ref('dim_mails') }} m
    inner join {{ ref('dim_clientes') }} dc
        on m.cliente_id_mail_phone = dc.cliente_id_mail_phone
    where m.cliente_id_mail_phone is not null
),

-- zona_id y distancia por dirección
direcciones_zona as (
    select direccion_id, zona_id, distancia_km as direccion_distancia_km
    from {{ ref('stg_clientes_direcciones') }}
),

zonas as (
    select
        zona_id,
        distancia_max_km as zona_distancia_max_km,
        demora_estimada_minutos as zona_demora_estimada
    from {{ ref('stg_zonas') }}
)

select
    -- ── Pedido ────────────────────────────────────────────────────────────────
    p.pedido_id,
    p.cliente_id,
    ci.cliente_id_mail_phone,
    p.direccion_id,

    -- ── Cliente ──────────────────────────────────────────────────────────────
    p.cliente_nombre,
    p.cliente_email,
    p.cliente_telefono,
    seg.segmento_cliente,

    -- ── Barrio (con fallback de int_clientes si no hay en el pedido) ─────────
    coalesce(p.barrio, ci.ultimo_barrio) as barrio,
    case
        when p.barrio is not null then 'pedido'
        when ci.ultimo_barrio is not null then 'cliente'
        else null
    end as barrio_origen,
    p.direccion,

    -- ── Zona ─────────────────────────────────────────────────────────────────
    dz.zona_id,
    p.costo_envio_zona,
    dz.direccion_distancia_km,
    z.zona_distancia_max_km,
    z.zona_demora_estimada,

    -- ── Fechas ───────────────────────────────────────────────────────────────
    p.created_at,
    p.fecha,
    p.semana,
    p.mes,
    p.anio,
    p.mes_num,
    p.dia_semana,
    p.hora,

    -- ── Tipo de pedido ───────────────────────────────────────────────────────
    p.tipo_retiro,
    p.tipo_pago,

    -- ── Montos ───────────────────────────────────────────────────────────────
    p.subtotal,
    p.descuento,
    p.descuento_ajuste,
    p.costo_envio,
    p.redondeo,
    p.total,

    -- ── MercadoPago ──────────────────────────────────────────────────────────
    p.mercadopago_id,
    p.mercadopago_status,
    p.mp_monto_transaccion,
    p.mp_monto_neto_recibido,
    p.mp_comision,

    -- ── Estado ───────────────────────────────────────────────────────────────
    p.estado_id,
    p.estado_nombre,
    p.is_pagado,
    p.is_activo,

    -- ── Delivery ─────────────────────────────────────────────────────────────
    p.repartidor,
    p.demora_minutos,
    p.distancia_km,

    -- ── Métricas del pedido ──────────────────────────────────────────────────
    p.cantidad_productos,
    p.cantidad_sabores,
    p.kg_total,

    -- ── Clima del día ────────────────────────────────────────────────────────
    cl.temperatura_maxima,
    cl.temperatura_minima,
    cl.temperatura_promedio,
    cl.quintil_temperatura,
    cl.categoria_temperatura,
    cl.flg_precipitaciones,
    cl.precipitacion_mm,
    cl.lluvia_mm,
    cl.quintil_precipitacion,
    cl.categoria_precipitacion,
    cl.viento_max_kmh,
    cl.quintil_viento,
    cl.categoria_viento,

    -- ── Comentarios ──────────────────────────────────────────────────────────
    p.comentario,
    p.motivo_cancelacion

from pedidos p
left join clima cl
    on cast(p.fecha as date) = cl.fecha
left join clientes_dedup ci
    on p.cliente_id = ci.cliente_id
left join segmentos seg
    on p.cliente_id = seg.cliente_id
left join direcciones_zona dz
    on p.direccion_id = dz.direccion_id
left join zonas z
    on dz.zona_id = z.zona_id
