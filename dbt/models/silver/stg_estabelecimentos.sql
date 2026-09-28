-- Um registro por estabelecimento (matriz ou filial). Campos de contato e endereço
-- ficam de fora de propósito: não são usados e são dados pessoais em muitos MEIs.
with origem as (
    select * from {{ bronze('estabelecimentos') }}
),

limpo as (
    select
        lpad(upper(trim(cnpj_basico)), 8, '0') as cnpj_basico,
        lpad(upper(trim(cnpj_ordem)), 4, '0') as cnpj_ordem,
        lpad(trim(cnpj_dv), 2, '0') as cnpj_dv,
        trim(identificador_matriz_filial) = '1' as eh_matriz,
        lpad(trim(situacao_cadastral), 2, '0') as situacao_cadastral,
        {{ data_receita('data_situacao_cadastral') }} as data_situacao_cadastral,
        lpad(trim(motivo_situacao_cadastral), 2, '0') as motivo_situacao_cadastral,
        {{ data_receita('data_inicio_atividade') }} as data_inicio_atividade,
        nullif(lpad(trim(cnae_fiscal_principal), 7, '0'), '0000000') as cnae_principal,
        nullif(upper(trim(uf)), '') as uf,
        nullif(trim(municipio), '') as municipio_codigo,
        _referencia as referencia
    from origem
)

select
    cnpj_basico || cnpj_ordem || cnpj_dv as cnpj,
    *
from limpo
