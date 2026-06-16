{# Lightweight surrogate-key generator (md5 of concatenated, null-safe fields).
   Re-implemented locally so the project needs no internet / no dbt packages. #}
{% macro generate_surrogate_key(field_list) %}
    md5(cast(concat_ws('||',
        {%- for field in field_list %}
        coalesce(cast({{ field }} as varchar), '_null_')
        {%- if not loop.last %},{% endif -%}
        {% endfor %}
    ) as varchar))
{% endmacro %}
