-- Entradas e saídas do MEI (SIMEI) por mês e UF.
-- Limitação: a Receita guarda só o período de MEI mais recente de cada empresa,
-- então reentradas antigas não aparecem. A série recente é a mais confiável.
with empresas as (
    select * from {{ ref('int_empresas') }}
    where data_opcao_mei is not null
),

eventos as (
    select date_trunc('month', data_opcao_mei) as mes, uf, regiao, setor, 1 as entradas, 0 as saidas
    from empresas

    union all

    select date_trunc('month', data_exclusao_mei), uf, regiao, setor, 0, 1
    from empresas
    where data_exclusao_mei is not null
)

select
    mes::date as mes,
    uf,
    regiao,
    setor,
    sum(entradas) as entradas_mei,
    sum(saidas) as saidas_mei
from eventos
where mes >= cast('{{ var("inicio_serie") }}' as date)
  and mes < {{ data_referencia() }}
group by all
