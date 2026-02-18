{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ ref('egresos') }}
),

renamed as (
    select
        row_number() over (order by fecha, descripcion) as egreso_id,
        cast(fecha as date) as fecha,
        descripcion,

        -- Normalizar categoria (unificar mayúsculas/minúsculas y variantes)
        case lower(trim(categoria))
            when 'insumos'                    then 'Insumos'
            when 'alimentos'                  then 'Insumos'
            when 'logistica'                  then 'Logistica'
            when 'inversion'                  then 'Inversion'
            when 'marketing'                  then 'Marketing'
            when 'mod'                        then 'Mano de obra'
            when 'mod jorge'                  then 'Mano de obra'
            when 'materiales y herramientas'  then 'Materiales y herramientas'
            when 'servicios'                  then 'Servicios'
            when 'inscripción'                then 'Inscripciones'
            when 'inscripciones'              then 'Inscripciones'
            when 'seguridad'                  then 'Seguridad'
            when 'impuestos'                  then 'Impuestos'
            when 'etiquetas bedual'           then 'Etiquetas'
            when 'alquiler'                   then 'Alquiler'
            when 'bromatologia'               then 'Bromatologia'
            when 'fumigacion'                 then 'Fumigacion'
            when 'potes'                      then 'Potes'
            when 'socios'                     then 'Socios'
            when 'comisiones'                 then 'Comisiones'
            when 'pago'                       then 'Pago'
            when 'indirecto'                  then 'Indirecto'
            when 'general'                    then 'General'
            when 'feria'                      then 'Feria'
            when 'otros'                      then 'Otros'
            when 'familia'                    then 'Otros'
            when 'licor'                      then 'Otros'
            when 'coche'                      then 'Otros'
            when 'taxi'                       then 'Otros'
            when 'suministros del hogar'      then 'Otros'
            when 'seguro'                     then 'Otros'
            when 'electricidad'               then 'Servicios'
            when 'ultimo cargado'             then 'Otros'
            else 'Otros'
        end as categoria,

        monto,
        moneda,

        -- Normalizar medio de pago
        case lower(trim(medio_pago))
            when 'efectivo'  then 'efectivo'
            when 'tc'        then 'tarjeta_credito'
            when 'tc mc'     then 'tarjeta_credito'
            when 'tc visa'   then 'tarjeta_credito'
            when 'mp'        then 'mercadopago'
            else 'otro'
        end as medio_pago,

        cantidad,

        -- Campos derivados
        extract(year from cast(fecha as date)) as anio,
        extract(month from cast(fecha as date)) as mes_num,
        strftime(cast(fecha as date), '%Y-%m') as mes

    from source
    where fecha is not null
)

select * from renamed
