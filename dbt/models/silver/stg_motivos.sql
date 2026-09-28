-- Motivos de situação cadastral, classificados pelo tipo de encerramento.
-- A distinção importa: a Receita faz baixas de ofício em massa (ex.: MEIs omissos
-- ou inaptos), que criam picos de "fechamento" que não foram decisão do empresário.
-- A classificação está no seed motivos_tipo_baixa (código a código, com justificativa);
-- motivos fora dele caem em "Outros" e o teste assert_motivos_classificados avisa se pesarem.
select
    lpad(trim(m.codigo), 2, '0') as motivo,
    trim(m.descricao) as motivo_descricao,
    coalesce(t.tipo_baixa, 'Outros') as tipo_baixa
from {{ bronze('motivos') }} as m
left join {{ ref('motivos_tipo_baixa') }} as t
    on lpad(trim(m.codigo), 2, '0') = t.motivo
