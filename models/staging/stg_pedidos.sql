{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('ainara_raw', 'pedidos') }}
),

renamed as (
    select
        -- IDs
        codigo as pedido_id,
        cliente as cliente_id,
        direccion as direccion_id,
        
        -- Tipo de pedido
        tipo_retiro,
        tipo_pago,
        
        -- Mercado Pago
        mp_ID as mercadopago_id,
        mp_Status as mercadopago_status,
        mp_TransactionAmount as mp_monto_transaccion,
        mp_totalPaidAmount as mp_monto_pagado,
        mp_netReceivedAmount as mp_monto_neto_recibido,
        mp_Fee as mp_comision,
        mp_PaymentType as mp_tipo_pago,
        
        -- Contacto
        telefono,
        comentario,
        
        -- Montos
        subtotal,
        redondeo,
        total,
        envio as costo_envio,
        descuento,
        descuento_ajuste,
        descuento_alianza,
        abona_con,
        
        -- Estado
        estado as estado_id,
        pagado as is_pagado,
        
        -- Delivery
        demora as demora_minutos,
        distancia as distancia_km,
        repartidor,
        
        -- Metadata
        activo as is_activo,
        motivo as motivo_cancelacion,
        
        -- Timestamps (convertir Unix timestamp a datetime)
        fecha_sys as created_at_unix,
        to_timestamp(fecha_sys) as created_at,
        to_timestamp(last_fecha_update) as updated_at,
        admin_insert as created_by_admin_id,
        last_admin_update as updated_by_admin_id

    from source
    where codigo is not null
)

select * from renamed
