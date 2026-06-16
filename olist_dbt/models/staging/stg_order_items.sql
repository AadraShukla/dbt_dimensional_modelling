with source as (
    select * from {{ source('raw', 'olist_order_items_dataset') }}
)

select
    order_id,
    cast(order_item_id as integer)            as order_item_id,
    product_id,
    seller_id,
    cast(nullif(shipping_limit_date, '') as timestamp) as shipping_limit_date,
    cast(price as double)                     as price,
    cast(freight_value as double)             as freight_value
from source
