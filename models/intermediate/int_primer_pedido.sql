{{
    config(
        materialized='view'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- int_primer_pedido: identifica el primer pedido por identidad (id_mail)
-- Usa dedup por email para que clientes con múltiples IDs compartan historial
-- ════════════════════════════════════════════════════════════════════════════

with pedidos as (
    select
        pedido_id,
        cliente_id,
        created_at
    from {{ ref('stg_pedidos') }}
    where estado_id != 4  -- excluir cancelados
),

-- Mapear cliente_id → id_mail (dedup por email)
clientes_dedup as (
    select
        cliente_id,
        id_mail
    from {{ ref('int_clientes') }}
),

pedidos_con_identidad as (
    select
        p.pedido_id,
        p.cliente_id,
        coalesce(c.id_mail, p.cliente_id * -1) as identidad,
        p.created_at,
        row_number() over (
            partition by coalesce(c.id_mail, p.cliente_id * -1)
            order by p.created_at, p.pedido_id
        ) as rn
    from pedidos p
    left join clientes_dedup c on p.cliente_id = c.cliente_id
),

primer_fechas as (
    select
        identidad,
        created_at as fecha_primer_pedido
    from pedidos_con_identidad
    where rn = 1
)

select
    pc.pedido_id,
    pc.cliente_id,
    pc.identidad,
    case when pc.rn = 1 then true else false end as is_primer_pedido,
    pf.fecha_primer_pedido
from pedidos_con_identidad pc
inner join primer_fechas pf on pc.identidad = pf.identidad
