{#- A Receita grava datas como 'AAAAMMDD' e usa '0'/'00000000' para vazio. -#}
{% macro data_receita(coluna) -%}
    case
        when {{ coluna }} is null or trim({{ coluna }}) in ('', '0', '00000000') then null
        else try_strptime(trim({{ coluna }}), '%Y%m%d')::date
    end
{%- endmacro %}

{#-
    Filtro das métricas de empresas: exclui os CNPJs de campanha eleitoral (natureza jurídica
    409-0, Candidato a Cargo Político Eletivo). Eles são abertos aos milhares em anos de eleição
    e baixados automaticamente em 31/12 (ex.: 463 mil baixas "voluntárias" em 31/12/2024),
    o que distorceria aberturas e fechamentos. Vão para o modelo gold_campanhas_eleitorais.
-#}
{% macro empresa_regular() -%}
    natureza_juridica is distinct from '4090'
{%- endmacro %}

{#- Primeiro dia do mês de referência da carga (pasta AAAA-MM da Receita). -#}
{% macro data_referencia() -%}
    cast('{{ var("referencia") }}-01' as date)
{%- endmacro %}

{#-
    Valor de um caractere para o cálculo do DV do CNPJ: código ASCII - 48.
    Funciona para o CNPJ numérico ('0'..'9' -> 0..9) e para o alfanumérico
    que a Receita adota desde julho/2026 ('A' -> 17, 'B' -> 18, ...).
-#}
{% macro valor_cnpj(expr, posicao) -%}
    (ascii(substr({{ expr }}, {{ posicao }}, 1)) - 48)
{%- endmacro %}

{#- Dígito verificador calculado sobre as primeiras len(pesos) posições (módulo 11). -#}
{% macro dv_cnpj(expr, pesos) -%}
    (case when (
        {%- for peso in pesos %}
        {{ valor_cnpj(expr, loop.index) }} * {{ peso }}{% if not loop.last %} +{% endif %}
        {%- endfor %}
    ) % 11 < 2 then 0 else 11 - (
        {%- for peso in pesos %}
        {{ valor_cnpj(expr, loop.index) }} * {{ peso }}{% if not loop.last %} +{% endif %}
        {%- endfor %}
    ) % 11 end)
{%- endmacro %}

{#-
    true se o CNPJ tem formato válido (12 posições [0-9A-Z] + 2 dígitos) e os dois
    dígitos verificadores conferem. Regra da IN RFB 2.229/2024, válida para os dois formatos.
-#}
{% macro cnpj_valido(expr) -%}
    coalesce(
        regexp_full_match({{ expr }}, '[0-9A-Z]{12}[0-9]{2}')
        and {{ dv_cnpj(expr, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]) }} = {{ valor_cnpj(expr, 13) }}
        and {{ dv_cnpj(expr, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]) }} = {{ valor_cnpj(expr, 14) }},
        false
    )
{%- endmacro %}
