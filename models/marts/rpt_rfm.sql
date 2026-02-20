{{
    config(
        materialized='table'
    )
}}

-- ════════════════════════════════════════════════════════════════════════════
-- rpt_rfm: RFM detallado para dashboard (solo clientes con compras)
-- ════════════════════════════════════════════════════════════════════════════

select
    cliente_id_mail_phone,
    cliente_id,
    nombre,
    email,
    tipo_cliente,
    tipo_identidad,
    barrio,

    -- Raw RFM values
    dias_desde_ultimo_pedido,
    total_pedidos,
    pedidos_por_semana,
    total_gastado,
    total_gastado_usd,
    kg_total,
    ticket_promedio,
    primer_pedido,
    ultimo_pedido,

    -- Scores
    recencia_score,
    frecuencia_score,
    monetario_score,
    rfm_total,

    -- Segment
    segmento_cliente,

    -- Labels descriptivos
    case recencia_score
        when 7 then '0-30 dias'
        when 6 then '31-60 dias'
        when 5 then '61-90 dias'
        when 4 then '91-180 dias'
        when 3 then '181-360 dias'
        when 2 then '361-720 dias'
        when 1 then '720+ dias'
        else 'Sin compras'
    end as recencia_label,

    case frecuencia_score
        when 6 then '1+ /semana'
        when 5 then '~quincenal'
        when 4 then '~mensual'
        when 3 then '~bimestral'
        when 2 then '~semestral'
        when 1 then '<semestral'
        else 'Sin compras'
    end as frecuencia_label,

    case monetario_score
        when 5 then 'Q5 (top KG)'
        when 4 then 'Q4'
        when 3 then 'Q3'
        when 2 then 'Q2'
        when 1 then 'Q1 (bajo KG)'
        else 'Sin compras'
    end as volumen_label,

    -- Preferences
    tipo_retiro_preferido,
    tipo_pago_preferido

from {{ ref('dim_clientes') }}
where total_pedidos > 0
