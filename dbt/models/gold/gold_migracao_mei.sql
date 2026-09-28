-- Para onde vão as empresas que deixam de ser MEI?
--   * Encerrou: foi baixada até 60 dias depois de sair do MEI (saiu porque fechou)
--   * Cresceu no Simples: continua no Simples Nacional como ME/EPP
--   * Ativa fora do Simples: segue ativa sem Simples. Pode ter migrado para Presumido/Real
--     ou ter sido excluída do Simples (ex.: por débitos); a base não permite distinguir.
--   * Inapta/suspensa/outros: demais casos (em geral, empresas paradas)
with ex_meis as (
    select * from {{ ref('int_empresas') }}
    where data_exclusao_mei is not null
      and data_exclusao_mei >= cast('{{ var("inicio_serie") }}' as date)
      and data_exclusao_mei < {{ data_referencia() }}
)

select
    year(data_exclusao_mei) as ano_saida,
    uf,
    regiao,
    setor,
    case
        when baixada and data_baixa <= data_exclusao_mei + interval 60 day then 'Encerrou'
        when optante_simples then 'Cresceu no Simples (ME/EPP)'
        when ativa then 'Ativa fora do Simples'
        else 'Inapta/suspensa/outros'
    end as destino,
    count(*) as empresas
from ex_meis
group by all
