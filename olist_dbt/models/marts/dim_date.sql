{{ config(materialized='table') }}

-- Conformed date dimension built from a DuckDB date spine covering the order
-- history. Grain: one row per calendar day.
with bounds as (
    select
        cast(min(order_purchase_timestamp) as date) as min_date,
        cast(max(order_purchase_timestamp) as date) as max_date
    from {{ ref('stg_orders') }}
),

spine as (
    select cast(unnest(generate_series(min_date, max_date, interval 1 day)) as date) as date_day
    from bounds
)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_sk,
    date_day,
    extract(year from date_day)        as year,
    extract(quarter from date_day)     as quarter,
    extract(month from date_day)       as month,
    strftime(date_day, '%B')           as month_name,
    extract(day from date_day)         as day_of_month,
    extract(dow from date_day)         as day_of_week,
    strftime(date_day, '%A')           as day_name,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from spine
