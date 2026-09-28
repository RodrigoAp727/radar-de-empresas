---
title: CNPJs de campanha eleitoral
---

Todo candidato recebe um CNPJ para movimentar os recursos da campanha (natureza jurídica
**409-0, Candidato a Cargo Político Eletivo**). Esses CNPJs são abertos aos milhares entre
agosto e setembro dos anos de eleição e **baixados automaticamente em 31 de dezembro**.

Na base da Receita, essas baixas aparecem como *encerramento voluntário*. Quem conta
"empresas abertas e fechadas" sem filtrá-los vê uma explosão de aberturas em anos eleitorais
e um pico de fechamentos no último dia do ano. Neste painel eles ficam **fora de todas as
métricas de empresas** e aparecem só aqui.

```sql por_ano
select
    cast(ano_eleicao as integer)::varchar as ano,
    sum(cnpjs_abertos) as cnpjs_abertos,
    sum(cnpjs_baixados) as cnpjs_baixados,
    sum(baixados_em_31_dez) as baixados_em_31_dez,
    sum(baixados_em_31_dez) / sum(cnpjs_abertos) as pct_baixados_31_dez
from radar.campanhas_eleitorais
group by 1
having sum(cnpjs_abertos) >= 1000
order by 1
```

<BarChart
    data={por_ano}
    x=ano
    y=cnpjs_abertos
    sort=false
    yFmt="#,##0"
    colorPalette={['#2a78d6']}
    title="CNPJs de campanha abertos por ano"
    subtitle="Picos nos anos de eleição (municipais e gerais)"
/>

<DataTable data={por_ano}>
    <Column id=ano title="Ano" />
    <Column id=cnpjs_abertos title="CNPJs abertos" fmt="#,##0" />
    <Column id=cnpjs_baixados title="Baixados" fmt="#,##0" />
    <Column id=baixados_em_31_dez title="Baixados em 31/12" fmt="#,##0" />
    <Column id=pct_baixados_31_dez title="% baixados em 31/12" fmt=pct1 />
</DataTable>

<small>Em 2020 a eleição foi adiada para novembro por causa da pandemia, e a baixa em lote
aconteceu em 28/02/2021 (557 mil CNPJs num único dia). Os CNPJs de 2026 ainda estão ativos
porque a campanha está em andamento.</small>
