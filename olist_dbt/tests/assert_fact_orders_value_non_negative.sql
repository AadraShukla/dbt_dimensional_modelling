-- Singular data test: no order should have a negative total value.
-- Returns offending rows; the test passes only when zero rows are returned.
select
    order_id,
    total_order_value
from {{ ref('fact_orders') }}
where total_order_value < 0
