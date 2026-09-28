-- Fotografia da base na data da carga, por UF e setor.
select
    '{{ var("referencia") }}' as referencia,
    uf,
    regiao,
    setor,
    count(*) filter (where ativa) as empresas_ativas,
    count(*) filter (where ativa and optante_mei) as mei_ativos,
    count(*) filter (where ativa and optante_simples and not optante_mei) as simples_me_epp_ativas,
    count(*) filter (where ativa and not optante_simples) as fora_do_simples_ativas,
    count(*) filter (where situacao_cadastral = '04') as inaptas,
    count(*) filter (where cnpj_alfanumerico) as cnpjs_alfanumericos
from {{ ref('int_empresas') }}
where {{ empresa_regular() }}
group by all
