-- Uma empresa não pode ser baixada antes de começar a funcionar.
-- A base tem alguns casos legados assim; o teste avisa e só falha se virar um volume relevante.
{{ config(warn_if='>0', error_if='>50000') }}

select cnpj, data_inicio_atividade, data_baixa
from {{ ref('int_empresas') }}
where data_baixa < data_inicio_atividade
