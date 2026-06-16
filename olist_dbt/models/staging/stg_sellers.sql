with source as (
    select * from {{ source('raw', 'olist_sellers_dataset') }}
)

select
    seller_id,
    cast(seller_zip_code_prefix as integer) as seller_zip_code_prefix,
    seller_city,
    upper(seller_state)                     as seller_state
from source
