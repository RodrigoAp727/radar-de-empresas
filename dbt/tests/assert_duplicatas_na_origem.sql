-- A camada silver deduplica empresas e Simples por raiz de CNPJ. Este teste mantém o
-- problema visível: avisa quantas raízes vieram repetidas da Receita, e falha se o
-- volume indicar erro de carga (ex.: o mesmo arquivo processado duas vezes).
{{ config(warn_if='>0', error_if='>1000') }}

with empresas as (
    select 'empresas' as tabela, cnpj_basico
    from {{ bronze('empresas') }}
    group by cnpj_basico
    having count(*) > 1
),

simples as (
    select 'simples' as tabela, cnpj_basico
    from {{ bronze('simples') }}
    group by cnpj_basico
    having count(*) > 1
)

select * from empresas
union all
select * from simples
