-- Tabela (não view): a deduplicação por janela é cara e o int_empresas lê isto inteiro.
{{ config(materialized='table') }}

-- Um registro por empresa (raiz do CNPJ). A razão social fica de fora:
-- em MEIs ela é o nome da pessoa física, e nenhuma análise precisa dela.
-- A origem traz raízes duplicadas raras (ex.: set/2026, uma cópia com natureza 0000 e
-- porte nulo). Fica o registro mais completo; o teste assert_duplicatas_na_origem avisa.
with origem as (
    select
        lpad(upper(trim(cnpj_basico)), 8, '0') as cnpj_basico,
        lpad(trim(natureza_juridica), 4, '0') as natureza_juridica,
        try_cast(replace(trim(capital_social), ',', '.') as decimal(18, 2)) as capital_social,
        lpad(trim(porte_empresa), 2, '0') as codigo_porte
    from {{ bronze('empresas') }}
)

select
    cnpj_basico,
    natureza_juridica,
    capital_social,
    case codigo_porte
        when '01' then 'Micro empresa'
        when '03' then 'Empresa de pequeno porte'
        when '05' then 'Demais'
        else 'Não informado'
    end as porte_empresa
from origem
qualify row_number() over (
    partition by cnpj_basico
    order by (natureza_juridica = '0000'), (codigo_porte is null), capital_social desc nulls last
) = 1
