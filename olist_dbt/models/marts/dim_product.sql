{{ config(materialized='table') }}

-- Product dimension. Grain: one row per product_id.
with products as (
    select * from {{ ref('stg_products') }}
)

select
    {{ generate_surrogate_key(['product_id']) }} as product_sk,
    product_id,
    product_category_name,
    product_category_name_english,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,
    product_photos_qty
from products
