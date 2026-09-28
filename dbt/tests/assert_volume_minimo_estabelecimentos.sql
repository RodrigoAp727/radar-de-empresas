-- Carga incompleta (download cortado, zip corrompido) costuma aparecer como queda de volume.
select count(*) as linhas
from {{ ref('stg_estabelecimentos') }}
having count(*) < {{ var('min_estabelecimentos') }}
