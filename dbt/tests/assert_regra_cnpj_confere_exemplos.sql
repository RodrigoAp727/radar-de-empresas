-- Testa a própria regra de validação: cada exemplo conhecido (seed cnpjs_exemplo)
-- precisa ser classificado como válido ou inválido exatamente como esperado.
select cnpj, caso, esperado_valido, {{ cnpj_valido('cnpj') }} as calculado
from {{ ref('cnpjs_exemplo') }}
where {{ cnpj_valido('cnpj') }} <> esperado_valido
