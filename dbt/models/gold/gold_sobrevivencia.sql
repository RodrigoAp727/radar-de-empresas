-- Sobrevivência por coorte de abertura: das empresas abertas no ano X, quantas
-- continuavam de pé N anos depois. Só entram no denominador as empresas que já
-- completaram N anos até a data da carga (quem é mais novo ainda não pode ser avaliado).
--
-- Duas medidas:
--   sobreviventes        = sem baixa até o prazo (definição cadastral, mais otimista)
--   sobreviventes_ativas = sem baixa E sem inaptidão até o prazo. Empresa inapta por omissão
--                          de declarações em geral já parou; esta é a medida mais realista.
with empresas as (
    select * from {{ ref('int_empresas') }}
    where {{ empresa_regular() }}
      and data_inicio_atividade >= cast('{{ var("inicio_serie") }}' as date)
      and data_inicio_atividade < {{ data_referencia() }}
),

horizontes as (
    select unnest([1, 2, 3, 5, 10]) as anos
)

select
    year(e.data_inicio_atividade) as ano_abertura,
    h.anos,
    e.uf,
    e.regiao,
    e.secao,
    e.setor,
    case when e.nasceu_mei then 'MEI' else 'Demais' end as perfil,
    count(*) as empresas_avaliadas,
    count(*) filter (
        where e.data_baixa is null
           or e.data_baixa >= e.data_inicio_atividade + to_years(h.anos)
    ) as sobreviventes,
    count(*) filter (
        where coalesce(e.data_baixa, e.data_inaptidao) is null
           or coalesce(e.data_baixa, e.data_inaptidao) >= e.data_inicio_atividade + to_years(h.anos)
    ) as sobreviventes_ativas
from empresas as e
cross join horizontes as h
where e.data_inicio_atividade + to_years(h.anos) <= {{ data_referencia() }}
group by all
