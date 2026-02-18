{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- dim_clientes: dimensión de clientes con RFM reworked
-- Recencia: 7 bandas, Frecuencia: 6 bandas (por semana), Monetario: quintiles
-- ════════════════════════════════════════════════════════════════════════════

with clientes as (
    select * from {{ ref('stg_clientes') }}
),

-- id_mail dedup desde int_clientes
clientes_enriquecidos as (
    select
        cliente_id,
        id_mail
    from {{ ref('int_clientes') }}
),

direcciones as (
    select * from {{ ref('stg_clientes_direcciones') }}
),

-- Métricas de pedidos por cliente (solo entregados)
pedidos_por_cliente as (
    select
        cliente_id,
        count(*) as total_pedidos,
        sum(total) as total_gastado,
        round(avg(total), 2) as ticket_promedio,
        sum(kg_total) as kg_total,
        min(created_at) as primer_pedido,
        max(created_at) as ultimo_pedido,
        count(case when tipo_retiro = 'delivery' then 1 end) as pedidos_delivery,
        count(case when tipo_retiro = 'local' then 1 end) as pedidos_local,
        count(case when tipo_retiro = 'mostrador' then 1 end) as pedidos_mostrador,
        count(case when tipo_pago = 'cash' then 1 end) as pagos_efectivo,
        count(case when tipo_pago = 'mp' then 1 end) as pagos_mercadopago,
        count(case when tipo_pago = 'transfer' then 1 end) as pagos_transferencia
    from {{ ref('fct_pedidos') }}
    where estado_id = 3
    group by cliente_id
),

-- Dirección principal (la más reciente)
direccion_principal as (
    select
        cliente_id,
        barrio,
        direccion,
        row_number() over (partition by cliente_id order by created_at desc) as rn
    from direcciones
    where is_activo = 1
),

-- Promedio USD del último pedido de cada cliente
usd_ultimo_pedido as (
    select
        fp.cliente_id,
        round(sum(fp.total_usd), 2) as total_gastado_usd
    from {{ ref('fct_pedidos') }} fp
    where fp.estado_id = 3
    group by fp.cliente_id
),

-- Calcular RFM raw
rfm_calc as (
    select
        pc.cliente_id,
        pc.total_pedidos,
        pc.total_gastado,
        pc.ticket_promedio,
        pc.kg_total,
        pc.primer_pedido,
        pc.ultimo_pedido,
        date_diff('day', pc.ultimo_pedido, current_date) as dias_desde_ultimo_pedido,

        -- Pedidos por semana desde primer pedido
        case
            when date_diff('week', pc.primer_pedido, current_date) > 0
            then pc.total_pedidos::float / date_diff('week', pc.primer_pedido, current_date)
            else pc.total_pedidos::float
        end as pedidos_por_semana,

        pc.pedidos_delivery,
        pc.pedidos_local,
        pc.pedidos_mostrador,
        pc.pagos_efectivo,
        pc.pagos_mercadopago,
        pc.pagos_transferencia
    from pedidos_por_cliente pc
),

-- Asignar scores RFM
rfm_scores as (
    select
        *,
        -- Recencia: 7 bandas
        case
            when dias_desde_ultimo_pedido <= 7   then 7
            when dias_desde_ultimo_pedido <= 15  then 6
            when dias_desde_ultimo_pedido <= 30  then 5
            when dias_desde_ultimo_pedido <= 60  then 4
            when dias_desde_ultimo_pedido <= 90  then 3
            when dias_desde_ultimo_pedido <= 180 then 2
            else 1
        end as recencia_score,

        -- Frecuencia: 6 bandas (pedidos por semana)
        case
            when pedidos_por_semana >= 1.0  then 6
            when pedidos_por_semana >= 0.5  then 5
            when pedidos_por_semana >= 0.25 then 4
            when pedidos_por_semana >= 0.1  then 3
            when pedidos_por_semana >= 0.04 then 2
            else 1
        end as frecuencia_score,

        -- Monetario: quintiles (1-5)
        ntile(5) over (order by total_gastado) as monetario_score
    from rfm_calc
)

select
    c.cliente_id,
    ce.id_mail,
    c.nombre,
    c.email,
    c.telefono,
    c.tipo_cliente,
    c.created_at as fecha_registro,
    c.is_activo,

    d.barrio,
    d.direccion as direccion_principal,

    -- Métricas de compra
    coalesce(r.total_pedidos, 0) as total_pedidos,
    coalesce(r.total_gastado, 0) as total_gastado,
    round(coalesce(r.ticket_promedio, 0), 2) as ticket_promedio,
    round(coalesce(r.kg_total, 0), 2) as kg_total,
    coalesce(u.total_gastado_usd, 0) as total_gastado_usd,
    r.primer_pedido,
    r.ultimo_pedido,
    coalesce(r.dias_desde_ultimo_pedido, 9999) as dias_desde_ultimo_pedido,
    round(coalesce(r.pedidos_por_semana, 0), 4) as pedidos_por_semana,

    -- Tipo retiro
    coalesce(r.pedidos_delivery, 0) as pedidos_delivery,
    coalesce(r.pedidos_local, 0) as pedidos_local,
    coalesce(r.pedidos_mostrador, 0) as pedidos_mostrador,
    case
        when coalesce(r.pedidos_delivery, 0) >= coalesce(r.pedidos_local, 0)
             and coalesce(r.pedidos_delivery, 0) >= coalesce(r.pedidos_mostrador, 0) then 'delivery'
        when coalesce(r.pedidos_local, 0) >= coalesce(r.pedidos_mostrador, 0) then 'local'
        else 'mostrador'
    end as tipo_retiro_preferido,

    -- Tipo pago
    coalesce(r.pagos_efectivo, 0) as pagos_efectivo,
    coalesce(r.pagos_mercadopago, 0) as pagos_mercadopago,
    coalesce(r.pagos_transferencia, 0) as pagos_transferencia,
    case
        when coalesce(r.pagos_efectivo, 0) >= coalesce(r.pagos_mercadopago, 0)
             and coalesce(r.pagos_efectivo, 0) >= coalesce(r.pagos_transferencia, 0) then 'efectivo'
        when coalesce(r.pagos_mercadopago, 0) >= coalesce(r.pagos_transferencia, 0) then 'mercadopago'
        else 'transferencia'
    end as tipo_pago_preferido,

    -- RFM scores
    coalesce(r.recencia_score, 0) as recencia_score,
    coalesce(r.frecuencia_score, 0) as frecuencia_score,
    coalesce(r.monetario_score, 0) as monetario_score,
    coalesce(r.recencia_score, 0) + coalesce(r.frecuencia_score, 0) + coalesce(r.monetario_score, 0) as rfm_total,

    -- Segmento
    case
        when coalesce(r.total_pedidos, 0) = 0 then 'Sin compras'
        when r.dias_desde_ultimo_pedido <= 30 and r.total_pedidos <= 2 then 'Nuevo'
        when r.recencia_score >= 6 and r.frecuencia_score >= 5 and r.monetario_score >= 4 then 'VIP'
        when r.recencia_score >= 5 and r.frecuencia_score >= 4 then 'Leal'
        when r.recencia_score >= 5 and r.monetario_score >= 3 and r.frecuencia_score <= 3 then 'Potencial'
        when r.recencia_score <= 3 and r.frecuencia_score >= 4 then 'En riesgo'
        when r.recencia_score <= 2 and r.frecuencia_score >= 3 then 'Dormido'
        when r.recencia_score <= 2 and r.frecuencia_score <= 2 then 'Perdido'
        else 'Ocasional'
    end as segmento_cliente

from clientes c
left join clientes_enriquecidos ce on c.cliente_id = ce.cliente_id
left join direccion_principal d on c.cliente_id = d.cliente_id and d.rn = 1
left join rfm_scores r on c.cliente_id = r.cliente_id
left join usd_ultimo_pedido u on c.cliente_id = u.cliente_id
