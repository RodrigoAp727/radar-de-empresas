-- Uma linha por empresa (estabelecimento matriz), já enriquecida com setor, região,
-- regime tributário e tipo de baixa. É a base de todos os modelos gold.
with matrizes as (
    select * from {{ ref('stg_estabelecimentos') }}
    where eh_matriz
)

select
    m.cnpj,
    m.cnpj_basico,
    regexp_matches(m.cnpj_basico, '[A-Z]') as cnpj_alfanumerico,

    m.data_inicio_atividade,
    m.situacao_cadastral,
    m.situacao_cadastral = '02' as ativa,
    m.situacao_cadastral = '08' as baixada,
    case when m.situacao_cadastral = '08' then m.data_situacao_cadastral end as data_baixa,
    case when m.situacao_cadastral = '08' then coalesce(mot.tipo_baixa, 'Outros') end as tipo_baixa,
    -- Inaptidão: a Receita declara inapta a empresa omissa (sobretudo motivo 63, omissão de
    -- declarações). Na base, é assim que a "limpeza" de ofício aparece, e não como baixa.
    m.situacao_cadastral = '04' as inapta,
    case when m.situacao_cadastral = '04' then m.data_situacao_cadastral end as data_inaptidao,
    m.situacao_cadastral = '04' and m.motivo_situacao_cadastral = '63' as inapta_por_omissao,

    m.cnae_principal,
    coalesce(sec.secao, '?') as secao,
    coalesce(sec.secao_curta, 'Não informado') as setor,

    m.uf,
    coalesce(uf.regiao, case when m.uf = 'EX' then 'Exterior' else 'Não informado' end) as regiao,

    emp.natureza_juridica,
    emp.porte_empresa,

    coalesce(sim.optante_simples, false) as optante_simples,
    sim.data_opcao_simples,
    sim.data_exclusao_simples,
    coalesce(sim.optante_mei, false) as optante_mei,
    sim.data_opcao_mei,
    sim.data_exclusao_mei,
    -- Aproximação: a Receita só guarda o período de MEI mais recente. Consideramos que a
    -- empresa "nasceu MEI" se esse período começou até 180 dias após a abertura.
    coalesce(
        sim.data_opcao_mei between m.data_inicio_atividade - interval 30 day
                               and m.data_inicio_atividade + interval 180 day,
        false
    ) as nasceu_mei

from matrizes as m
left join {{ ref('cnae_secoes') }} as sec
    on try_cast(substr(m.cnae_principal, 1, 2) as integer) between sec.divisao_inicio and sec.divisao_fim
left join {{ ref('ufs') }} as uf
    on m.uf = uf.uf
left join {{ ref('stg_motivos') }} as mot
    on m.motivo_situacao_cadastral = mot.motivo
left join {{ ref('stg_empresas') }} as emp
    on m.cnpj_basico = emp.cnpj_basico
left join {{ ref('stg_simples') }} as sim
    on m.cnpj_basico = sim.cnpj_basico
