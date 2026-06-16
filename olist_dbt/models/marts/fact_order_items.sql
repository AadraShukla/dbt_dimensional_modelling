{{ config(materialized='table') }}

-- ================================================================
-- fact_order_items -- line-level fact sharing the same conformed dims
-- Grain: ONE ROW PER ORDER LINE ITEM (order_id + order_item_id).
-- Foreign keys -> dim_customer, dim_product, dim_seller, dim_date.
-- Enables product- and seller-level analysis that the order-grain
-- fact_orders cannot answer.
-- ================================================================
with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
)

select
    {{ generate_surrogate_key(['i.order_id', 'i.order_item_id']) }} as order_item_sk,
    i.order_id,
    i.order_item_id,

    -- foreign keys
    {{ generate_surrogate_key(['o.customer_id']) }} as customer_sk,
    {{ generate_surrogate_key(['i.product_id']) }}  as product_sk,
    {{ generate_surrogate_key(['i.seller_id']) }}   as seller_sk,
    cast(strftime(o.order_purchase_timestamp, '%Y%m%d') as integer) as order_date_sk,

    o.order_status,

    -- measures
    i.price,
    i.freight_value,
    i.price + i.freight_value as item_total
from items i
inner join orders o on i.order_id = o.order_id
