with source as (
    select * from {{ source('raw', 'olist_customers_dataset') }}
)

select
    customer_id,
    customer_unique_id,
    cast(customer_zip_code_prefix as integer) as customer_zip_code_prefix,
    customer_city,
    upper(customer_state)                     as customer_state
from source
