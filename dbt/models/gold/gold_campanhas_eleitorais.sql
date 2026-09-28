-- CNPJs de campanha eleitoral (natureza jurídica 409-0, Candidato a Cargo Político Eletivo).
-- Cada candidato recebe um CNPJ para a campanha, que é baixado automaticamente em 31/12
-- do ano da eleição. Ficam fora das métricas de empresas e aparecem só aqui.
select
    year(data_inicio_atividade) as ano_eleicao,
    uf,
    regiao,
    count(*) as cnpjs_abertos,
    count(*) filter (where baixada) as cnpjs_baixados,
    count(*) filter (where baixada and month(data_baixa) = 12 and day(data_baixa) = 31) as baixados_em_31_dez,
    count(*) filter (where ativa) as cnpjs_ativos
from {{ ref('int_empresas') }}
where natureza_juridica = '4090'
  and data_inicio_atividade >= cast('{{ var("inicio_serie") }}' as date)
group by all
