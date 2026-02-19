{{
    config(
        materialized='view'
    )
}}

with clientes as (
    select * from {{ ref('stg_clientes') }}
),

-- ── identidad desde dim_mails (fuente única) ─────────────────────────────────
mails as (
    select
        cliente_id,
        cliente_id_mail_phone
    from {{ ref('dim_mails') }}
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

-- ── Dedup por identidad: rankear cliente_ids dentro de cada identidad ────────
clientes_por_identidad as (
    select
        m.cliente_id_mail_phone,
        m.cliente_id,
        row_number() over (
            partition by m.cliente_id_mail_phone
            order by c.created_at desc, m.cliente_id desc
        ) as rn_identidad,
        count(*) over (partition by m.cliente_id_mail_phone) as total_clientes_identidad
    from mails m
    inner join clientes c on m.cliente_id = c.cliente_id
    where m.cliente_id_mail_phone is not null
),

-- ── Lista de cliente_ids anteriores por identidad ────────────────────────────
anteriores_por_identidad as (
    select
        cliente_id_mail_phone,
        string_agg(cast(cliente_id as varchar), ', ' order by cliente_id) as cliente_ids_anteriores
    from clientes_por_identidad
    where rn_identidad > 1
    group by cliente_id_mail_phone
)

select
    -- Datos del cliente
    c.cliente_id,
    m.cliente_id_mail_phone,
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

    -- Cantidad de cliente_ids asociados a esta identidad
    coalesce(ci.total_clientes_identidad, 0) as total_clientes_identidad,

    -- Es el ultimo cliente_id de esta identidad? (1 = si, 0 = no)
    case
        when ci.rn_identidad = 1 then 1
        when ci.rn_identidad is null then 1  -- sin identidad = es único
        else 0
    end as is_ultimo_cliente_identidad,

    -- IDs anteriores de esta identidad (solo si hay duplicados)
    ai.cliente_ids_anteriores,

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
left join mails m
    on c.cliente_id = m.cliente_id
left join clientes_por_identidad ci
    on c.cliente_id = ci.cliente_id
left join anteriores_por_identidad ai
    on m.cliente_id_mail_phone = ai.cliente_id_mail_phone
    and ci.rn_identidad = 1  -- solo mostrar anteriores en el registro más reciente
left join ultima_direccion ud
    on c.cliente_id = ud.cliente_id
left join direccion_anterior da
    on c.cliente_id = da.cliente_id
left join zona_metricas zm
    on c.cliente_id = zm.cliente_id
