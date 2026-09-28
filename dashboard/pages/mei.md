---
title: MEI e Simples Nacional
---

O MEI é a porta de entrada da maioria das empresas brasileiras. Esta página acompanha quantos
MEIs entram e saem do regime por região e para onde vão as empresas que deixam de ser MEI.

```sql retrato
select
    sum(mei_ativos) as mei_ativos,
    sum(simples_me_epp_ativas) as simples_me_epp,
    sum(fora_do_simples_ativas) as fora_do_simples,
    sum(mei_ativos) / sum(empresas_ativas) as pct_mei
from radar.retrato_uf
```

<Grid cols=4>
    <BigValue data={retrato} value=mei_ativos title="MEIs ativos" fmt="#,##0" />
    <BigValue data={retrato} value=pct_mei title="MEIs entre as empresas ativas" fmt=pct1 />
    <BigValue data={retrato} value=simples_me_epp title="ME/EPP no Simples" fmt="#,##0" />
    <BigValue data={retrato} value=fora_do_simples title="Fora do Simples" fmt="#,##0" />
</Grid>

## Novos MEIs por região

```sql entradas_regiao
select
    date_trunc('quarter', mes) as trimestre,
    regiao,
    sum(entradas_mei) as entradas
from radar.mei_mensal
where regiao in ('Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul')
group by all
order by trimestre
```

<LineChart
    data={entradas_regiao}
    x=trimestre
    y=entradas
    series=regiao
    yFmt="#,##0"
    colorPalette={['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']}
    title="Novos MEIs por trimestre"
    subtitle="Com base na data de opção pelo SIMEI"
/>

## Para onde vão as empresas que deixam de ser MEI

Uma empresa sai do MEI por três caminhos: fecha, cresce (passa a faturar mais que o limite e vira
ME ou EPP no Simples) ou segue ativa fora do Simples (por migração para o Presumido/Real ou por exclusão, que a base não distingue). A proporção que cresce é um termômetro de
quantos microempreendedores conseguem escalar o negócio.

```sql migracao
select
    cast(ano_saida as integer)::varchar as ano_saida,
    destino,
    sum(empresas) as empresas
from radar.migracao_mei
group by all
order by ano_saida
```

<BarChart
    data={migracao}
    x=ano_saida
    y=empresas
    series=destino
    type=stacked100
    colorPalette={['#2a78d6', '#eb6834', '#1baf7a', '#eda100']}
    seriesOrder={['Cresceu no Simples (ME/EPP)', 'Ativa fora do Simples', 'Encerrou', 'Inapta/suspensa/outros']}
    title="Destino de quem saiu do MEI, por ano de saída"
/>

```sql migracao_setor
with limites as (select max(ano_saida) as ultimo from radar.migracao_mei)
select
    setor,
    sum(empresas) filter (where destino = 'Cresceu no Simples (ME/EPP)') / sum(empresas) as pct_cresceu,
    sum(empresas) as sairam_do_mei
from radar.migracao_mei, limites
where ano_saida >= ultimo - 2
  and setor <> 'Não informado'
group by setor
having sum(empresas) >= 1000
order by pct_cresceu desc
```

<DataTable data={migracao_setor} rows=25 title="Setores onde mais MEIs cresceram (últimos 3 anos)">
    <Column id=setor title="Setor" />
    <Column id=sairam_do_mei title="Saíram do MEI" fmt="#,##0" />
    <Column id=pct_cresceu title="% que cresceu para ME/EPP" fmt=pct1 />
</DataTable>
