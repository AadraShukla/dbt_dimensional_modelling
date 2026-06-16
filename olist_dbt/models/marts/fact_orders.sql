{{ config(materialized='table') }}

-- ================================================================
-- fact_orders  --  the central fact of the star schema
-- Grain: ONE ROW PER ORDER.
-- Foreign keys -> dim_customer, dim_date.
-- Measures: order value, freight, payment, review, delivery performance.
-- ================================================================
with orders as (
    select * from {{ ref('stg_orders') }}
),

metrics as (
    select * from {{ ref('int_order_metrics') }}
)

select
    -- surrogate / degenerate keys
    {{ generate_surrogate_key(['o.order_id']) }} as order_sk,
    o.order_id,

    -- foreign keys to dimensions
    {{ generate_surrogate_key(['o.customer_id']) }} as customer_sk,
    cast(strftime(o.order_purchase_timestamp, '%Y%m%d') as integer) as order_date_sk,

    -- degenerate dimension
    o.order_status,

    -- dates
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    -- measures
    m.items_count,
    m.total_price,
    m.total_freight,
    m.total_price + m.total_freight as total_order_value,
    m.total_payment,
    m.max_installments,
    m.avg_review_score,
    m.review_count,

    -- delivery performance measures
    date_diff('day', o.order_purchase_timestamp, o.order_delivered_customer_date) as delivery_days,
    case
        when o.order_delivered_customer_date is null then null
        when o.order_delivered_customer_date <= o.order_estimated_delivery_date then true
        else false
    end as delivered_on_time
from orders o
left join metrics m on o.order_id = m.order_id
