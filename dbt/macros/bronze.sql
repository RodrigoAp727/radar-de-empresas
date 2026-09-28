{#- Lê uma tabela da camada bronze (Parquet gerado por pipeline/bronze.py). -#}
{% macro bronze(tabela) -%}
    read_parquet('{{ env_var("RADAR_DATA_DIR", "../data") }}/bronze/{{ tabela }}/*.parquet')
{%- endmacro %}
