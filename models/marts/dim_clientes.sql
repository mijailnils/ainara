{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- dim_clientes: dimensión de clientes agrupada por identidad
-- Clave: cliente_id_mail_phone (de dim_mails)
-- Múltiples cliente_id con misma identidad se unifican en 1 fila
-- Recencia: 7 bandas, Frecuencia: 6 bandas (por semana), Monetario: quintiles
-- ════════════════════════════════════════════════════════════════════════════

with clientes as (
    select * from {{ ref('stg_clientes') }}
),

-- Mapeo cliente_id → cliente_id_mail_phone desde dim_mails
mails as (
    select cliente_id, cliente_id_mail_phone, tipo_identidad
    from {{ ref('dim_mails') }}
),

-- Asignar identidad a cada cliente
clientes_con_identidad as (
    select
        c.*,
        m.cliente_id_mail_phone,
        m.tipo_identidad
    from clientes c
    left join mails m on c.cliente_id = m.cliente_id
),

-- Representante: el cliente_id más reciente por identidad
representante as (
    select
        cliente_id_mail_phone,
        tipo_identidad,
        cliente_id,
        nombre,
        email,
        telefono,
        tipo_cliente,
        created_at,
        is_activo,
        row_number() over (
            partition by cliente_id_mail_phone
            order by created_at desc, cliente_id desc
        ) as rn
    from clientes_con_identidad
    where cliente_id_mail_phone is not null
),

-- Todos los cliente_ids por identidad
todos_ids as (
    select
        cliente_id_mail_phone,
        string_agg(cast(cliente_id as varchar), ', ' order by cliente_id) as todos_cliente_ids,
        count(*) as n_cliente_ids
    from clientes_con_identidad
    where cliente_id_mail_phone is not null
    group by cliente_id_mail_phone
),

direcciones as (
    select * from {{ ref('stg_clientes_direcciones') }}
),

-- Dirección principal (la más reciente entre todos los cliente_ids de la identidad)
direccion_principal as (
    select
        ci.cliente_id_mail_phone,
        d.barrio,
        d.direccion,
        row_number() over (partition by ci.cliente_id_mail_phone order by d.created_at desc) as rn
    from clientes_con_identidad ci
    inner join direcciones d on ci.cliente_id = d.cliente_id
    where d.is_activo = 1
      and ci.cliente_id_mail_phone is not null
),

-- Pedidos agregados por identidad (solo entregados)
pedidos_por_identidad as (
    select
        m.cliente_id_mail_phone,
        count(*) as total_pedidos,
        sum(fp.total) as total_gastado,
        round(avg(fp.total), 2) as ticket_promedio,
        sum(fp.kg_total) as kg_total,
        sum(fp.total_usd) as total_gastado_usd,
        min(fp.created_at) as primer_pedido,
        max(fp.created_at) as ultimo_pedido,
        count(case when fp.tipo_retiro = 'delivery' then 1 end) as pedidos_delivery,
        count(case when fp.tipo_retiro = 'local' then 1 end) as pedidos_local,
        count(case when fp.tipo_retiro = 'mostrador' then 1 end) as pedidos_mostrador,
        count(case when fp.tipo_pago = 'cash' then 1 end) as pagos_efectivo,
        count(case when fp.tipo_pago = 'mp' then 1 end) as pagos_mercadopago,
        count(case when fp.tipo_pago = 'transfer' then 1 end) as pagos_transferencia
    from {{ ref('fct_pedidos') }} fp
    inner join mails m on fp.cliente_id = m.cliente_id
    where fp.estado_id = 3
      and m.cliente_id_mail_phone is not null
    group by m.cliente_id_mail_phone
),

-- Calcular RFM raw
rfm_calc as (
    select
        pi.*,
        date_diff('day', pi.ultimo_pedido, current_date) as dias_desde_ultimo_pedido,
        case
            when date_diff('week', pi.primer_pedido, current_date) > 0
            then pi.total_pedidos::float / date_diff('week', pi.primer_pedido, current_date)
            else pi.total_pedidos::float
        end as pedidos_por_semana
    from pedidos_por_identidad pi
),

-- Asignar scores RFM
rfm_scores as (
    select
        *,
        -- Recencia: 7 bandas
        case
            when dias_desde_ultimo_pedido <= 30   then 7
            when dias_desde_ultimo_pedido <= 60   then 6
            when dias_desde_ultimo_pedido <= 90   then 5
            when dias_desde_ultimo_pedido <= 180  then 4
            when dias_desde_ultimo_pedido <= 360  then 3
            when dias_desde_ultimo_pedido <= 720  then 2
            else 1
        end as recencia_score,

        -- Frecuencia: 6 bandas (pedidos por semana)
        case
            when pedidos_por_semana >= 1.0   then 6
            when pedidos_por_semana >= 0.25  then 5
            when pedidos_por_semana >= 0.1   then 4
            when pedidos_por_semana >= 0.05  then 3
            when pedidos_por_semana >= 0.01  then 2
            else 1
        end as frecuencia_score,

        -- Volumen KG: quintiles (1-5)
        ntile(5) over (order by kg_total) as monetario_score
    from rfm_calc
)

select
    rep.cliente_id_mail_phone,
    rep.tipo_identidad,
    rep.cliente_id,
    ti.todos_cliente_ids,
    ti.n_cliente_ids,
    rep.nombre,
    rep.email,
    rep.telefono,
    rep.tipo_cliente,
    rep.created_at as fecha_registro,
    rep.is_activo,

    dp.barrio,
    dp.direccion as direccion_principal,

    -- Métricas de compra (agregadas por identidad)
    coalesce(r.total_pedidos, 0) as total_pedidos,
    coalesce(r.total_gastado, 0) as total_gastado,
    round(coalesce(r.ticket_promedio, 0), 2) as ticket_promedio,
    round(coalesce(r.kg_total, 0), 2) as kg_total,
    coalesce(r.total_gastado_usd, 0) as total_gastado_usd,
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

from representante rep
left join todos_ids ti on rep.cliente_id_mail_phone = ti.cliente_id_mail_phone
left join direccion_principal dp on rep.cliente_id_mail_phone = dp.cliente_id_mail_phone and dp.rn = 1
left join rfm_scores r on rep.cliente_id_mail_phone = r.cliente_id_mail_phone
where rep.rn = 1
