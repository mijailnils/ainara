{{
    config(
        materialized='table'
    )
}}

with pedidos as (
    select * from {{ ref('fct_pedidos') }}
    where estado_id = 3  -- Solo entregados
)

select
    fecha,
    semana,
    mes,
    anio,
    mes_num,
    
    -- Métricas de pedidos
    count(*) as total_pedidos,
    count(distinct cliente_id) as clientes_unicos,
    
    -- Métricas de ventas
    sum(total) as venta_total,
    sum(subtotal) as subtotal_total,
    sum(descuento) as descuento_total,
    sum(costo_envio) as envio_total,
    round(avg(total), 2) as ticket_promedio,
    
    -- Por tipo de retiro
    count(case when tipo_retiro = 'delivery' then 1 end) as pedidos_delivery,
    count(case when tipo_retiro = 'local' then 1 end) as pedidos_local,
    count(case when tipo_retiro = 'mostrador' then 1 end) as pedidos_mostrador,
    
    -- Por tipo de pago
    count(case when tipo_pago = 'cash' then 1 end) as pagos_efectivo,
    count(case when tipo_pago = 'mp' then 1 end) as pagos_mercadopago,
    count(case when tipo_pago = 'transfer' then 1 end) as pagos_transferencia,
    
    -- Ventas por tipo de pago
    sum(case when tipo_pago = 'cash' then total else 0 end) as venta_efectivo,
    sum(case when tipo_pago = 'mp' then total else 0 end) as venta_mercadopago,
    sum(case when tipo_pago = 'transfer' then total else 0 end) as venta_transferencia,
    
    -- MercadoPago
    sum(mp_comision) as comision_mp_total,
    sum(mp_monto_neto_recibido) as neto_mp_total,
    
    -- Productos y sabores
    sum(cantidad_productos) as productos_vendidos,
    sum(cantidad_sabores) as sabores_vendidos

from pedidos
group by fecha, semana, mes, anio, mes_num
order by fecha desc