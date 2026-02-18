{{
    config(
        materialized='view'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- stg_dolar_blue: tipo de cambio blue diario con forward-fill
-- Fuente: investing.com (solo días hábiles) → rellenamos fines de semana/feriados
-- ════════════════════════════════════════════════════════════════════════════

with source as (
    select
        cast(fecha as date) as fecha,
        cast(valor_blue as decimal(10,2)) as valor_blue
    from {{ ref('dolar_blue') }}
),

-- Date spine continuo de min a max fecha
date_spine as (
    select unnest(generate_series(
        (select min(fecha) from source),
        (select max(fecha) from source),
        interval '1 day'
    ))::date as fecha
),

-- Left join y forward-fill
joined as (
    select
        ds.fecha,
        s.valor_blue
    from date_spine ds
    left join source s on ds.fecha = s.fecha
)

select
    fecha,
    coalesce(
        valor_blue,
        last_value(valor_blue ignore nulls) over (order by fecha rows unbounded preceding)
    ) as valor_blue
from joined
