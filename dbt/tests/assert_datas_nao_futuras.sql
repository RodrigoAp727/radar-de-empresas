-- Datas de abertura depois da data da carga indicam erro de digitação na origem.
{{ config(warn_if='>0', error_if='>1000') }}

select cnpj, data_inicio_atividade
from {{ ref('int_empresas') }}
where data_inicio_atividade > {{ data_referencia() }} + interval 1 month
