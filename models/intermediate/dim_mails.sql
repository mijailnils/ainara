{{
    config(
        materialized='view'
    )
}}

with todos_clientes as (
    select * from {{ ref('stg_clientes') }}
),

-- Clientes con email
con_email as (
    select *
    from todos_clientes
    where email is not null and email != ''
),

-- ID único por cada email distinto
emails_unicos as (
    select
        email,
        row_number() over (order by email) as id_mail
    from con_email
    group by email
),

-- Teléfonos que ya tienen al menos un registro con email
telefonos_con_email as (
    select distinct telefono
    from con_email
    where telefono is not null and telefono != ''
),

-- Clientes sin email, solo si su teléfono NO aparece en un registro con email
sin_email as (
    select *
    from todos_clientes c
    where (c.email is null or c.email = '')
      and not exists (
          select 1
          from telefonos_con_email te
          where te.telefono = c.telefono
      )
),

-- Unir ambos grupos
resultado as (
    -- Clientes con email → tienen id_mail
    select
        em.id_mail,
        em.email,
        c.cliente_id,
        c.nombre,
        c.telefono,
        c.is_activo,
        c.created_at
    from emails_unicos em
    inner join con_email c on em.email = c.email

    union all

    -- Clientes sin email cuyo teléfono no está asociado a ningún email
    select
        null as id_mail,
        null as email,
        s.cliente_id,
        s.nombre,
        s.telefono,
        s.is_activo,
        s.created_at
    from sin_email s
)

select *
from resultado
order by id_mail nulls last, created_at desc
