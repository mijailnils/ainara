{{
    config(
        materialized='view'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- dim_mails: resolución de identidad de clientes
-- Campo clave: cliente_id_mail_phone
--   1. Email primero: clientes con mismo email → misma identidad
--   2. Phone bridge: si un teléfono pertenece a un cliente con email,
--      clientes sin email con ese teléfono heredan esa identidad
--   3. Phone-only: clientes sin email, agrupados por teléfono
--   4. Sin email ni teléfono → NULL (no identificable)
--
-- Fuentes de teléfono: stg_clientes + stg_pedidos (el más frecuente)
-- ════════════════════════════════════════════════════════════════════════════

with todos_clientes as (
    select * from {{ ref('stg_clientes') }}
),

-- ═══ PASO 0: Unificar teléfonos (clientes + pedidos) ═══════════════════════

-- Teléfono desde stg_clientes (preferido), normalizado con TRIM
phone_clientes as (
    select cliente_id, trim(telefono) as telefono
    from todos_clientes
    where telefono is not null and trim(telefono) != ''
),

-- Teléfono más frecuente desde stg_pedidos (fallback), normalizado con TRIM
phone_pedidos_ranked as (
    select
        cliente_id,
        trim(telefono) as telefono,
        count(*) as n_usos,
        row_number() over (
            partition by cliente_id
            order by count(*) desc, trim(telefono)
        ) as rn
    from {{ ref('stg_pedidos') }}
    where telefono is not null and trim(telefono) != ''
      and cliente_id not in (0, 1)  -- excluir catch-all clients
    group by cliente_id, trim(telefono)
),

phone_pedidos as (
    select cliente_id, telefono
    from phone_pedidos_ranked
    where rn = 1
),

-- Teléfono unificado: preferir clientes, fallback pedidos
phone_unificado as (
    select
        c.cliente_id,
        coalesce(pc.telefono, pp.telefono) as telefono
    from todos_clientes c
    left join phone_clientes pc on c.cliente_id = pc.cliente_id
    left join phone_pedidos pp on c.cliente_id = pp.cliente_id
),

-- ═══ PASO 1: Identidad por EMAIL ═══════════════════════════════════════════

con_email as (
    select *
    from todos_clientes
    where email is not null and email != ''
),

-- ID único por cada email distinto (positivo: 1, 2, 3, ...)
emails_unicos as (
    select
        email,
        row_number() over (order by email) as id_mail
    from con_email
    group by email
),

-- ═══ PASO 2: Phone bridge (sin email → hereda email via teléfono) ══════════

-- Todos los teléfonos asociados a clientes CON email
phones_de_email_clients as (
    select distinct pu.telefono, eu.id_mail
    from con_email ce
    inner join phone_unificado pu on ce.cliente_id = pu.cliente_id
    inner join emails_unicos eu on ce.email = eu.email
    where pu.telefono is not null
),

-- Clientes SIN email cuyo teléfono matchea con un cliente CON email
-- → heredan el id_mail
phone_bridge_ranked as (
    select
        pu.cliente_id,
        pec.id_mail,
        row_number() over (partition by pu.cliente_id order by pec.id_mail) as rn
    from phone_unificado pu
    inner join phones_de_email_clients pec on pu.telefono = pec.telefono
    inner join todos_clientes c on pu.cliente_id = c.cliente_id
    where (c.email is null or c.email = '')
      and pu.telefono is not null
),

phone_to_mail as (
    select cliente_id, id_mail
    from phone_bridge_ranked
    where rn = 1
),

-- ═══ PASO 3: Phone-only identity ═══════════════════════════════════════════
-- Clientes sin email Y sin bridge a email, pero CON teléfono

-- Clientes ya resueltos (tienen email o fueron bridgeados)
clientes_resueltos as (
    select cliente_id from con_email
    union
    select cliente_id from phone_to_mail
),

-- Teléfonos únicos de clientes no resueltos → identidad por teléfono
-- Usamos IDs negativos (-1, -2, -3, ...) para diferenciar de email IDs
phones_sin_email as (
    select
        pu.telefono,
        -(row_number() over (order by pu.telefono)) as id_phone
    from phone_unificado pu
    where pu.telefono is not null
      and pu.cliente_id not in (select cliente_id from clientes_resueltos)
    group by pu.telefono
),

-- ═══ RESULTADO ═════════════════════════════════════════════════════════════

resultado as (
    -- Grupo 1: Clientes con email → identidad por email
    select
        eu.id_mail as cliente_id_mail_phone,
        eu.id_mail,
        null::bigint as id_phone,
        'email' as tipo_identidad,
        c.cliente_id,
        eu.email,
        pu.telefono,
        c.nombre,
        c.is_activo,
        c.created_at
    from emails_unicos eu
    inner join con_email c on eu.email = c.email
    left join phone_unificado pu on c.cliente_id = pu.cliente_id

    union all

    -- Grupo 2: Sin email, phone bridge → hereda identidad de email
    select
        pm.id_mail as cliente_id_mail_phone,
        pm.id_mail,
        null::bigint as id_phone,
        'phone_bridge' as tipo_identidad,
        c.cliente_id,
        null as email,
        pu.telefono,
        c.nombre,
        c.is_activo,
        c.created_at
    from phone_to_mail pm
    inner join todos_clientes c on pm.cliente_id = c.cliente_id
    left join phone_unificado pu on c.cliente_id = pu.cliente_id

    union all

    -- Grupo 3: Sin email, sin bridge, con teléfono → identidad por teléfono
    select
        pse.id_phone as cliente_id_mail_phone,
        null::bigint as id_mail,
        pse.id_phone,
        'phone_only' as tipo_identidad,
        c.cliente_id,
        null as email,
        pu.telefono,
        c.nombre,
        c.is_activo,
        c.created_at
    from phone_unificado pu
    inner join phones_sin_email pse on pu.telefono = pse.telefono
    inner join todos_clientes c on pu.cliente_id = c.cliente_id
    where pu.cliente_id not in (select cliente_id from clientes_resueltos)

    union all

    -- Grupo 4: Sin email, sin teléfono → no identificable
    select
        null::bigint as cliente_id_mail_phone,
        null::bigint as id_mail,
        null::bigint as id_phone,
        'sin_identidad' as tipo_identidad,
        c.cliente_id,
        null as email,
        null as telefono,
        c.nombre,
        c.is_activo,
        c.created_at
    from todos_clientes c
    left join phone_unificado pu on c.cliente_id = pu.cliente_id
    where (c.email is null or c.email = '')
      and c.cliente_id not in (select cliente_id from clientes_resueltos)
      and (pu.telefono is null)
)

select *
from resultado
order by cliente_id_mail_phone nulls last, created_at desc
