{{ config(materialized='table') }}

-- Customer dimension. Grain: one row per order-scoped customer_id.
-- customer_unique_id lets you roll up to the real person across orders.
with customers as (
    select * from {{ ref('stg_customers') }}
)

select
    {{ generate_surrogate_key(['customer_id']) }} as customer_sk,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
from customers
