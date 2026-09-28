select
    lpad(trim(codigo), 7, '0') as cnae,
    trim(descricao) as cnae_descricao
from {{ bronze('cnaes') }}
