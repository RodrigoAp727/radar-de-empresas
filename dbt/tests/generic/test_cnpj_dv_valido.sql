{#- Falha para cada CNPJ com formato inválido ou dígito verificador errado (numérico ou alfanumérico). -#}
{% test cnpj_dv_valido(model, column_name) %}

select {{ column_name }} as cnpj
from {{ model }}
where {{ column_name }} is not null
  and not {{ cnpj_valido(column_name) }}

{% endtest %}
