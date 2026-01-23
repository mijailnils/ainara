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
    
    -- Comentarios
    p.comentario,
    p.motivo_cancelacion

from pedidos p
left join clientes c on p.cliente_id = c.cliente_id
left join direcciones d on p.direccion_id = d.direccion_id
left join zonas z on d.zona_id = z.zona_id
left join productos_por_pedido pp on p.pedido_id = pp.pedido_id
left join sabores_por_pedido sp on p.pedido_id = sp.pedido_id
where p.is_activo = 1