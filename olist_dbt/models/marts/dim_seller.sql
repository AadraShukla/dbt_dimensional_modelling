{{ config(materialized='table') }}

-- Seller dimension. Grain: one row per seller_id.
with sellers as (
    select * from {{ ref('stg_sellers') }}
)

select
    {{ generate_surrogate_key(['seller_id']) }} as seller_sk,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
from sellers
