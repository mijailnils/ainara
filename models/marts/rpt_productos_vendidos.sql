{{
    config(
        materialized='table'
    )
}}

with productos_pedidos as (
    select
        pp.producto_id,
        pp.pedido_id
    from {{ ref('stg_pedidos_productos') }} pp
    inner join {{ ref('stg_pedidos') }} p 
        on pp.pedido_id = p.pedido_id
    where p.is_activo = 1
      and p.estado_id = 3  -- Entregados
),

productos as (
    select * from {{ ref('stg_productos') }}
),

categorias as (
    select * from {{ ref('stg_productos_categorias') }}
),

conteo as (
    select
        producto_id,
        count(*) as veces_vendido,
        count(distinct pedido_id) as pedidos_distintos
    from productos_pedidos
    group by producto_id
)

select
    p.producto_id,
    p.nombre as producto,
    c.nombre as categoria,
    p.precio_base,
    p.cantidad_gustos,
    
    coalesce(ct.veces_vendido, 0) as veces_vendido,
    coalesce(ct.pedidos_distintos, 0) as pedidos_distintos,
    
    coalesce(ct.veces_vendido, 0) * p.precio_base as ingreso_estimado,
    
    row_number() over (order by coalesce(ct.veces_vendido, 0) desc) as ranking,
    
    round(100.0 * coalesce(ct.veces_vendido, 0) / nullif(sum(ct.veces_vendido) over (), 0), 2) as porcentaje_del_total

from productos p
left join categorias c on p.categoria_id = c.categoria_id
left join conteo ct on p.producto_id = ct.producto_id
where p.is_activo = 1
order by veces_vendido desc