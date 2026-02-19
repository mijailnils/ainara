{{
    config(
        materialized='view'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- int_primer_pedido: identifica el primer pedido por identidad
-- Usa cliente_id_mail_phone de dim_mails como clave de identidad
-- ════════════════════════════════════════════════════════════════════════════

with pedidos as (
    select
        pedido_id,
        cliente_id,
        created_at
    from {{ ref('stg_pedidos') }}
    where estado_id != 4  -- excluir cancelados
),

-- Mapear cliente_id → cliente_id_mail_phone
identidades as (
    select
        cliente_id,
        cliente_id_mail_phone
    from {{ ref('dim_mails') }}
),

pedidos_con_identidad as (
    select
        p.pedido_id,
        p.cliente_id,
        i.cliente_id_mail_phone,
        p.created_at,
        row_number() over (
            partition by i.cliente_id_mail_phone
            order by p.created_at, p.pedido_id
        ) as rn
    from pedidos p
    left join identidades i on p.cliente_id = i.cliente_id
    where i.cliente_id_mail_phone is not null
),

primer_fechas as (
    select
        cliente_id_mail_phone,
        created_at as fecha_primer_pedido
    from pedidos_con_identidad
    where rn = 1
)

select
    pc.pedido_id,
    pc.cliente_id,
    pc.cliente_id_mail_phone,
    case when pc.rn = 1 then true else false end as is_primer_pedido,
    pf.fecha_primer_pedido
from pedidos_con_identidad pc
inner join primer_fechas pf on pc.cliente_id_mail_phone = pf.cliente_id_mail_phone
