with source as (
    select * from {{ source('raw', 'olist_products_dataset') }}
),

translation as (
    select * from {{ source('raw', 'product_category_name_translation') }}
)

select
    s.product_id,
    s.product_category_name,
    coalesce(t.product_category_name_english, 'unknown') as product_category_name_english,
    cast(s.product_weight_g as integer)  as product_weight_g,
    cast(s.product_length_cm as integer) as product_length_cm,
    cast(s.product_height_cm as integer) as product_height_cm,
    cast(s.product_width_cm as integer)  as product_width_cm,
    cast(s.product_photos_qty as integer) as product_photos_qty
from source s
left join translation t
    on s.product_category_name = t.product_category_name
