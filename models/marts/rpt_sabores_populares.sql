{{
    config(
        materialized='table'
    )
}}

with sabores_pedidos as (
    select
        pps.sabor_id,
        pp.pedido_id
    from {{ ref('stg_pedidos_productos_sabores') }} pps
    inner join {{ ref('stg_pedidos_productos') }} pp 
        on pps.pedido_producto_id = pp.pedido_producto_id
    inner join {{ ref('stg_pedidos') }} p 
        on pp.pedido_id = p.pedido_id
    where p.is_activo = 1
      and p.estado_id = 3  -- Entregados
),

sabores as (
    select * from {{ ref('stg_sabores') }}
),

categorias as (
    select * from {{ ref('stg_sabores_categorias') }}
),

conteo as (
    select
        sabor_id,
        count(*) as veces_pedido,
        count(distinct pedido_id) as pedidos_distintos
    from sabores_pedidos
    group by sabor_id
)

select
    s.sabor_id,
    s.nombre as sabor,
    c.nombre as categoria,
    s.is_sin_azucar,
    
    coalesce(ct.veces_pedido, 0) as veces_pedido,
    coalesce(ct.pedidos_distintos, 0) as pedidos_distintos,
    
    row_number() over (order by coalesce(ct.veces_pedido, 0) desc) as ranking,
    
    round(100.0 * coalesce(ct.veces_pedido, 0) / nullif(sum(ct.veces_pedido) over (), 0), 2) as porcentaje_del_total

from sabores s
left join categorias c on s.categoria_id = c.categoria_id
left join conteo ct on s.sabor_id = ct.sabor_id
where s.is_activo = 1
order by veces_pedido desc