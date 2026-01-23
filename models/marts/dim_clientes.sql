{{
    config(
        materialized='table'
    )
}}

with clientes as (
    select * from {{ ref('stg_clientes') }}
),

direcciones as (
    select * from {{ ref('stg_clientes_direcciones') }}
),

pedidos as (
    select * from {{ ref('stg_pedidos') }}
    where is_activo = 1
),

-- Métricas de pedidos por cliente
pedidos_por_cliente as (
    select
        cliente_id,
        count(*) as total_pedidos,
        sum(total) as total_gastado,
        avg(total) as ticket_promedio,
        min(created_at) as primer_pedido,
        max(created_at) as ultimo_pedido,
        count(case when tipo_retiro = 'delivery' then 1 end) as pedidos_delivery,
        count(case when tipo_retiro = 'local' then 1 end) as pedidos_local,
        count(case when tipo_retiro = 'mostrador' then 1 end) as pedidos_mostrador,
        count(case when tipo_pago = 'cash' then 1 end) as pagos_efectivo,
        count(case when tipo_pago = 'mp' then 1 end) as pagos_mercadopago,
        count(case when tipo_pago = 'transfer' then 1 end) as pagos_transferencia
    from pedidos
    group by cliente_id
),

-- Dirección principal (la más usada o última)
direccion_principal as (
    select 
        cliente_id,
        barrio,
        direccion,
        row_number() over (partition by cliente_id order by created_at desc) as rn
    from direcciones
    where is_activo = 1
),

-- Calcular RFM
rfm_calc as (
    select
        cliente_id,
        total_pedidos,
        total_gastado,
        ticket_promedio,
        primer_pedido,
        ultimo_pedido,
        date_diff('day', ultimo_pedido, current_date) as dias_desde_ultimo_pedido,
        pedidos_delivery,
        pedidos_local,
        pedidos_mostrador,
        pagos_efectivo,
        pagos_mercadopago,
        pagos_transferencia
    from pedidos_por_cliente
),

-- Asignar scores RFM (1-5, donde 5 es mejor)
rfm_scores as (
    select
        *,
        case 
            when dias_desde_ultimo_pedido <= 30 then 5
            when dias_desde_ultimo_pedido <= 60 then 4
            when dias_desde_ultimo_pedido <= 90 then 3
            when dias_desde_ultimo_pedido <= 180 then 2
            else 1
        end as recencia_score,
        case 
            when total_pedidos >= 20 then 5
            when total_pedidos >= 10 then 4
            when total_pedidos >= 5 then 3
            when total_pedidos >= 2 then 2
            else 1
        end as frecuencia_score,
        case 
            when total_gastado >= 100000 then 5
            when total_gastado >= 50000 then 4
            when total_gastado >= 20000 then 3
            when total_gastado >= 10000 then 2
            else 1
        end as monetario_score
    from rfm_calc
)

select
    c.cliente_id,
    c.nombre,
    c.email,
    c.telefono,
    c.tipo_cliente,
    c.created_at as fecha_registro,
    c.is_activo,
    
    d.barrio,
    d.direccion as direccion_principal,
    
    coalesce(r.total_pedidos, 0) as total_pedidos,
    coalesce(r.total_gastado, 0) as total_gastado,
    round(coalesce(r.ticket_promedio, 0), 2) as ticket_promedio,
    r.primer_pedido,
    r.ultimo_pedido,
    coalesce(r.dias_desde_ultimo_pedido, 9999) as dias_desde_ultimo_pedido,
    
    coalesce(r.pedidos_delivery, 0) as pedidos_delivery,
    coalesce(r.pedidos_local, 0) as pedidos_local,
    coalesce(r.pedidos_mostrador, 0) as pedidos_mostrador,
    case 
        when coalesce(r.pedidos_delivery, 0) >= coalesce(r.pedidos_local, 0) 
             and coalesce(r.pedidos_delivery, 0) >= coalesce(r.pedidos_mostrador, 0) then 'delivery'
        when coalesce(r.pedidos_local, 0) >= coalesce(r.pedidos_mostrador, 0) then 'local'
        else 'mostrador'
    end as tipo_retiro_preferido,
    
    coalesce(r.pagos_efectivo, 0) as pagos_efectivo,
    coalesce(r.pagos_mercadopago, 0) as pagos_mercadopago,
    coalesce(r.pagos_transferencia, 0) as pagos_transferencia,
    case 
        when coalesce(r.pagos_efectivo, 0) >= coalesce(r.pagos_mercadopago, 0) 
             and coalesce(r.pagos_efectivo, 0) >= coalesce(r.pagos_transferencia, 0) then 'efectivo'
        when coalesce(r.pagos_mercadopago, 0) >= coalesce(r.pagos_transferencia, 0) then 'mercadopago'
        else 'transferencia'
    end as tipo_pago_preferido,
    
    coalesce(r.recencia_score, 1) as recencia_score,
    coalesce(r.frecuencia_score, 1) as frecuencia_score,
    coalesce(r.monetario_score, 1) as monetario_score,
    coalesce(r.recencia_score, 1) + coalesce(r.frecuencia_score, 1) + coalesce(r.monetario_score, 1) as rfm_total,
    
    case
        when coalesce(r.total_pedidos, 0) = 0 then 'Sin compras'
        when r.recencia_score >= 4 and r.frecuencia_score >= 4 and r.monetario_score >= 4 then 'VIP'
        when r.recencia_score >= 4 and r.frecuencia_score >= 3 then 'Leal'
        when r.recencia_score >= 4 and r.frecuencia_score <= 2 then 'Nuevo'
        when r.recencia_score <= 2 and r.frecuencia_score >= 3 then 'En riesgo'
        when r.recencia_score <= 2 and r.frecuencia_score <= 2 then 'Perdido'
        else 'Regular'
    end as segmento_cliente

from clientes c
left join direccion_principal d on c.cliente_id = d.cliente_id and d.rn = 1
left join rfm_scores r on c.cliente_id = r.cliente_id