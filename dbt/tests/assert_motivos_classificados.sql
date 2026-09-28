-- Se mais de 20% das baixas dos últimos 3 anos caírem em "Outros", a regra de
-- classificação em stg_motivos precisa de revisão (a Receita pode ter criado motivos novos).
{{ config(severity='warn') }}

with recentes as (
    select tipo_baixa
    from {{ ref('int_empresas') }}
    where baixada
      and data_baixa >= {{ data_referencia() }} - interval 3 year
)

select
    count(*) filter (where tipo_baixa = 'Outros') / count(*) as proporcao_outros
from recentes
having count(*) > 0
   and count(*) filter (where tipo_baixa = 'Outros') / count(*) > 0.20
