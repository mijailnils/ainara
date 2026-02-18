{{
    config(
        materialized='table'
    )
}}

with pedidos as (
    select * from {{ ref('stg_pedidos') }}
),

clientes as (
    select * from {{ ref('stg_clientes') }}
),

direcciones as (
    select * from {{ ref('stg_clientes_direcciones') }}
),

zonas as (
    select * from {{ ref('stg_zonas') }}
),

-- Contar productos por pedido
productos_por_pedido as (
    select
        pedido_id,
        count(*) as cantidad_productos
    from {{ ref('stg_pedidos_productos') }}
    group by pedido_id
),

-- Contar sabores por pedido
sabores_por_pedido as (
    select
        pp.pedido_id,
        count(distinct pps.sabor_id) as cantidad_sabores
    from {{ ref('stg_pedidos_productos') }} pp
    left join {{ ref('stg_pedidos_productos_sabores') }} pps
        on pp.pedido_producto_id = pps.pedido_producto_id
    group by pp.pedido_id
),

-- Sumar kg por pedido (peso_kg por producto × cantidad de items)
kg_por_pedido as (
    select
        pp.pedido_id,
        sum(pr.peso_kg) as kg_total
    from {{ ref('stg_pedidos_productos') }} pp
    join {{ ref('stg_productos') }} pr on pp.producto_id = pr.producto_id
    group by pp.pedido_id
),

-- Costos por pedido
costos as (
    select * from {{ ref('int_costos_pedido') }}
),

-- Dolar blue
dolar as (
    select * from {{ ref('stg_dolar_blue') }}
),

-- Primer pedido flag
primer_pedido as (
    select pedido_id, is_primer_pedido, fecha_primer_pedido
    from {{ ref('int_primer_pedido') }}
)

select
    -- IDs
    p.pedido_id,
    p.cliente_id,
    p.direccion_id,
    
    -- Info del cliente
    c.nombre as cliente_nombre,
    c.email as cliente_email,
    c.telefono as cliente_telefono,
    
    -- Info de dirección
    d.barrio,
    d.direccion,
    z.precio_envio as costo_envio_zona,
    
    -- Fechas
    p.created_at,
    date_trunc('day', p.created_at) as fecha,
    date_trunc('week', p.created_at) as semana,
    date_trunc('month', p.created_at) as mes,
    year(p.created_at) as anio,
    month(p.created_at) as mes_num,
    dayofweek(p.created_at) as dia_semana,
    hour(p.created_at) as hora,

    -- Estación argentina
    case
        when month(p.created_at) in (12, 1, 2) then 'Verano'
        when month(p.created_at) in (3, 4, 5)  then 'Otoño'
        when month(p.created_at) in (6, 7, 8)  then 'Invierno'
        when month(p.created_at) in (9, 10, 11) then 'Primavera'
    end as estacion,

    -- Temporada comercial
    case
        when month(p.created_at) in (11, 12, 1, 2) then 'Alta'
        when month(p.created_at) in (4, 5, 6, 7, 8) then 'Baja'
        else 'Media'
    end as temporada,

    -- Horario del dia
    case
        when hour(p.created_at) between 10 and 13 then 'Mediodia'
        when hour(p.created_at) between 14 and 17 then 'Tarde'
        when hour(p.created_at) between 18 and 21 then 'Noche'
        when hour(p.created_at) between 22 and 23 then 'Trasnoche'
        else 'Otro'
    end as horario,
    
    -- Tipo de pedido
    p.tipo_retiro,
    p.tipo_pago,
    
    -- Montos
    p.subtotal,
    p.descuento,
    p.descuento_ajuste,
    p.costo_envio,
    p.redondeo,
    p.total,
    
    -- MercadoPago
    p.mercadopago_id,
    p.mercadopago_status,
    p.mp_monto_transaccion,
    p.mp_monto_neto_recibido,
    p.mp_comision,
    
    -- Estado
    p.estado_id,
    case p.estado_id
        when 1 then 'Pendiente'
        when 2 then 'En preparación'
        when 3 then 'Entregado'
        when 4 then 'Cancelado'
        else 'Otro'
    end as estado_nombre,
    p.is_pagado,
    p.is_activo,
    
    -- Delivery
    p.repartidor,
    p.demora_minutos,
    p.distancia_km,
    
    -- Métricas del pedido
    coalesce(pp.cantidad_productos, 0) as cantidad_productos,
    coalesce(sp.cantidad_sabores, 0) as cantidad_sabores,
    coalesce(kp.kg_total, 0) as kg_total,

    -- Costos y contribución
    coalesce(cs.costo_ingredientes, 0) as costo_ingredientes,
    coalesce(cs.costo_potes, 0) as costo_potes,
    coalesce(cs.costo_bolsa, 0) as costo_bolsa,
    coalesce(cs.costo_total, 0) as costo_total,
    p.total - coalesce(cs.costo_total, 0) as contribucion_mg,
    case
        when p.total > 0
        then round(100.0 * (p.total - coalesce(cs.costo_total, 0)) / p.total, 1)
        else 0
    end as margen_pct,

    -- Primer pedido
    coalesce(ppf.is_primer_pedido, false) as is_primer_pedido,

    -- USD (tipo de cambio blue del día)
    round(p.total / nullif(db.valor_blue, 0), 2) as total_usd,
    round(coalesce(cs.costo_total, 0) / nullif(db.valor_blue, 0), 2) as costo_total_usd,
    round((p.total - coalesce(cs.costo_total, 0)) / nullif(db.valor_blue, 0), 2) as contribucion_mg_usd,

    -- Comentarios
    p.comentario,
    p.motivo_cancelacion

from pedidos p
left join clientes c on p.cliente_id = c.cliente_id
left join direcciones d on p.direccion_id = d.direccion_id
left join zonas z on d.zona_id = z.zona_id
left join productos_por_pedido pp on p.pedido_id = pp.pedido_id
left join sabores_por_pedido sp on p.pedido_id = sp.pedido_id
left join kg_por_pedido kp on p.pedido_id = kp.pedido_id
left join costos cs on p.pedido_id = cs.pedido_id
left join dolar db on cast(p.created_at as date) = db.fecha
left join primer_pedido ppf on p.pedido_id = ppf.pedido_id
--where p.is_activo = 1