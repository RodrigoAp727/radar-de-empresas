-- Aberturas, fechamentos (baixas) e inaptidões de empresas por mês, UF e setor.
-- Só meses completos: o mês da carga fica de fora porque ainda está sendo preenchido.
with empresas as (
    select * from {{ ref('int_empresas') }}
    where {{ empresa_regular() }}
),

eventos as (
    select
        date_trunc('month', data_inicio_atividade) as mes,
        uf, regiao, secao, setor, nasceu_mei,
        1 as aberturas,
        0 as fechamentos,
        0 as fechamentos_voluntarios,
        0 as fechamentos_de_oficio,
        0 as inaptidoes,
        0 as inaptidoes_por_omissao
    from empresas
    where data_inicio_atividade is not null

    union all

    select
        date_trunc('month', data_baixa),
        uf, regiao, secao, setor, nasceu_mei,
        0, 1, (tipo_baixa = 'Voluntária')::int, (tipo_baixa = 'De ofício')::int, 0, 0
    from empresas
    where baixada and data_baixa is not null

    union all

    select
        date_trunc('month', data_inaptidao),
        uf, regiao, secao, setor, nasceu_mei,
        0, 0, 0, 0, 1, inapta_por_omissao::int
    from empresas
    where inapta and data_inaptidao is not null
)

select
    mes::date as mes,
    uf,
    regiao,
    secao,
    setor,
    case when nasceu_mei then 'MEI' else 'Demais' end as perfil,
    sum(aberturas) as aberturas,
    sum(fechamentos) as fechamentos,
    sum(fechamentos_voluntarios) as fechamentos_voluntarios,
    sum(fechamentos_de_oficio) as fechamentos_de_oficio,
    sum(fechamentos) - sum(fechamentos_voluntarios) - sum(fechamentos_de_oficio) as fechamentos_outros,
    sum(inaptidoes) as inaptidoes,
    sum(inaptidoes_por_omissao) as inaptidoes_por_omissao
from eventos
where mes >= cast('{{ var("inicio_serie") }}' as date)
  and mes < {{ data_referencia() }}
group by all
