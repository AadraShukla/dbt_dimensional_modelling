{{ config(materialized='view') }}

-- Intermediate: collapse line items, payments and reviews to one row per order
-- so they can be joined onto the order-grain fact without fan-out.
with items as (
    select
        order_id,
        count(*)            as items_count,
        sum(price)          as total_price,
        sum(freight_value)  as total_freight
    from {{ ref('stg_order_items') }}
    group by order_id
),

payments as (
    select
        order_id,
        sum(payment_value)        as total_payment,
        max(payment_installments) as max_installments
    from {{ ref('stg_order_payments') }}
    group by order_id
),

reviews as (
    select
        order_id,
        avg(cast(review_score as double)) as avg_review_score,
        count(*)                          as review_count
    from {{ ref('stg_order_reviews') }}
    group by order_id
)

select
    coalesce(i.order_id, p.order_id, r.order_id) as order_id,
    coalesce(i.items_count, 0)        as items_count,
    coalesce(i.total_price, 0)        as total_price,
    coalesce(i.total_freight, 0)      as total_freight,
    coalesce(p.total_payment, 0)      as total_payment,
    coalesce(p.max_installments, 0)   as max_installments,
    r.avg_review_score,
    coalesce(r.review_count, 0)       as review_count
from items i
full outer join payments p on i.order_id = p.order_id
full outer join reviews  r on coalesce(i.order_id, p.order_id) = r.order_id
