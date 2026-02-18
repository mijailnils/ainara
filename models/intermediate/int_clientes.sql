{{
    config(
        materialized='view'
    )
}}

with clientes as (
    select * from {{ ref('stg_clientes') }}
),

direcciones as (
    select * from {{ ref('stg_clientes_direcciones') }}
),

-- ── Direcciones rankeadas por cliente (más reciente primero) ─────────────────
dirs_ranked as (
    select
        *,
        row_number() over (
            partition by cliente_id
            order by created_at desc, direccion_id desc
        ) as rn
    from direcciones
),

ultima_direccion as (
    select * from dirs_ranked where rn = 1
),

direccion_anterior as (
    select * from dirs_ranked where rn = 2
),

zonas as (
    select
        zona_id,
        distancia_max_km,
        demora_estimada_minutos
    from {{ ref('stg_zonas') }}
),

-- ── Métricas de zona por cliente (todas sus direcciones) ────────────────────
zona_metricas as (
    select
        d.cliente_id,
        max(z.demora_estimada_minutos) as demora_estimada_max,
        min(z.demora_estimada_minutos) as demora_estimada_min,
        round(avg(z.demora_estimada_minutos), 1) as demora_estimada_avg,
        max(z.distancia_max_km) as distancia_max_km_max,
        min(z.distancia_max_km) as distancia_max_km_min,
        round(avg(z.distancia_max_km), 1) as distancia_max_km_avg
    from direcciones d
    inner join zonas z on d.zona_id = z.zona_id
    group by d.cliente_id
),

-- ── ID de mail: un ID único por cada email distinto ──────────────────────────
emails_unicos as (
    select
        email,
        row_number() over (order by email) as id_mail
    from clientes
    where email is not null and email != ''
    group by email
),

-- ── Clientes por email: rankear para detectar duplicados ─────────────────────
clientes_por_email as (
    select
        c.cliente_id,
        c.email,
        row_number() over (
            partition by c.email
            order by c.created_at desc, c.cliente_id desc
        ) as rn_email,
        count(*) over (partition by c.email) as total_clientes_email
    from clientes c
    where c.email is not null and c.email != ''
),

-- ── Lista de cliente_ids anteriores por email ────────────────────────────────
anteriores_por_email as (
    select
        email,
        string_agg(cast(cliente_id as varchar), ', ' order by cliente_id) as cliente_ids_anteriores
    from clientes_por_email
    where rn_email > 1
    group by email
)

select
    -- Datos del cliente
    c.cliente_id,
    em.id_mail,
    c.nombre,
    c.email,
    c.telefono,
    c.google_id,
    c.tipo_cliente,
    c.is_activo,
    c.created_at,
    c.updated_at,

    -- Barrios
    ud.barrio as ultimo_barrio,
    da.barrio as barrio_anterior,

    -- Cantidad de cliente_ids asociados a este email
    coalesce(ce.total_clientes_email, 0) as total_clientes_email,

    -- Es el ultimo cliente_id de este email? (1 = si, 0 = no)
    case
        when ce.rn_email = 1 then 1
        when ce.rn_email is null then 1  -- sin email = es único
        else 0
    end as is_ultimo_cliente_email,

    -- IDs anteriores de este email (solo si hay duplicados)
    ae.cliente_ids_anteriores as email_cliente_ids_anteriores,

    -- Última dirección
    ud.direccion_id as direccion_ultima_id,
    ud.direccion as direccion_ultima,
    ud.piso as direccion_ultima_piso,
    ud.depto as direccion_ultima_depto,
    ud.barrio as direccion_ultima_barrio,
    ud.latitud as direccion_ultima_lat,
    ud.longitud as direccion_ultima_lng,
    ud.distancia_km as direccion_ultima_distancia_km,
    ud.zona_id as direccion_ultima_zona_id,

    -- Dirección anterior (null si solo tiene una)
    da.direccion_id as direccion_anterior_id,
    da.direccion as direccion_anterior,
    da.barrio as direccion_anterior_barrio,
    da.zona_id as direccion_anterior_zona_id,

    -- Métricas de zona (sobre todas las direcciones del cliente)
    zm.demora_estimada_max,
    zm.demora_estimada_min,
    zm.demora_estimada_avg,
    zm.distancia_max_km_max,
    zm.distancia_max_km_min,
    zm.distancia_max_km_avg

from clientes c
left join emails_unicos em
    on c.email = em.email
left join clientes_por_email ce
    on c.cliente_id = ce.cliente_id
left join anteriores_por_email ae
    on c.email = ae.email
    and ce.rn_email = 1  -- solo mostrar anteriores en el registro más reciente
left join ultima_direccion ud
    on c.cliente_id = ud.cliente_id
left join direccion_anterior da
    on c.cliente_id = da.cliente_id
left join zona_metricas zm
    on c.cliente_id = zm.cliente_id
