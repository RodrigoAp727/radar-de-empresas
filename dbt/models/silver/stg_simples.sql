-- Tabela (não view): a deduplicação por janela é cara e o int_empresas lê isto inteiro.
{{ config(materialized='table') }}

-- Situação no Simples Nacional e no SIMEI. A Receita guarda só o período mais
-- recente de cada regime: uma empresa que entrou e saiu duas vezes aparece com as datas da última.
with origem as (
    select
        lpad(upper(trim(cnpj_basico)), 8, '0') as cnpj_basico,
        upper(trim(opcao_simples)) = 'S' as optante_simples,
        {{ data_receita('data_opcao_simples') }} as data_opcao_simples,
        {{ data_receita('data_exclusao_simples') }} as data_exclusao_simples,
        upper(trim(opcao_mei)) = 'S' as optante_mei,
        {{ data_receita('data_opcao_mei') }} as data_opcao_mei,
        {{ data_receita('data_exclusao_mei') }} as data_exclusao_mei
    from {{ bronze('simples') }}
)

select *
from origem
-- Se a origem repetir uma raiz, fica o registro com a opção mais recente.
qualify row_number() over (
    partition by cnpj_basico
    order by greatest(data_opcao_simples, data_opcao_mei) desc nulls last
) = 1
