---
title: Baixas e inaptidões
---

Uma empresa pode deixar de funcionar de dois jeitos na base do CNPJ:

- **Baixa** (situação 08): o CNPJ é encerrado. Na base atual, **mais de 99% das baixas estão
  registradas como "extinção por encerramento voluntário"**. A baixa de ofício, feita pela
  própria Receita, quase não aparece como baixa.
- **Inaptidão** (situação 04): a Receita declara inapta a empresa que deixou de entregar
  declarações (motivo 63, *omissão de declarações*). O CNPJ continua existindo, mas a empresa
  fica irregular. **É aqui que aparece a "limpeza" de ofício da Receita**, em lotes quase anuais
  (e 2025 praticamente não teve lote, o que distorce comparações de 2026 contra o ano anterior).

Olhar só as baixas subestima quantas empresas pararam de funcionar.

```sql ufs
select distinct uf from radar.aberturas_fechamentos
where uf is not null and uf <> 'EX'
order by uf
```

<Dropdown name=uf data={ufs} value=uf title="Estado" defaultValue="%">
    <DropdownOption value="%" valueLabel="Brasil" />
</Dropdown>

```sql por_mes
select
    mes,
    sum(fechamentos) as "Baixas",
    sum(inaptidoes) as "Inaptidões"
from radar.aberturas_fechamentos
where uf like '${inputs.uf.value}'
  and mes >= '2018-01-01'
group by mes
order by mes
```

<BarChart
    data={por_mes}
    x=mes
    y={['Baixas', 'Inaptidões']}
    type=stacked
    yFmt="#,##0"
    colorPalette={['#2a78d6', '#eb6834']}
    chartAreaHeight=320
    title="Baixas e inaptidões por mês"
    subtitle="Inaptidões vêm em lotes: são ações da Receita, não decisões dos empresários"
/>

```sql omissao_ano
select
    year(mes)::varchar as ano,
    sum(inaptidoes) as inaptidoes,
    sum(inaptidoes_por_omissao) / nullif(sum(inaptidoes), 0) as pct_omissao
from radar.aberturas_fechamentos
where uf like '${inputs.uf.value}'
  and mes >= '2018-01-01'
group by 1
order by 1
```

<DataTable data={omissao_ano} title="Inaptidões por ano">
    <Column id=ano title="Ano" />
    <Column id=inaptidoes title="Empresas declaradas inaptas" fmt="#,##0" />
    <Column id=pct_omissao title="Por omissão de declarações" fmt=pct1 />
</DataTable>

## Setores com maior alta de baixas nos últimos 12 meses

```sql baixas_setor
with limites as (select max(mes) as fim from radar.aberturas_fechamentos),
base as (
    select
        setor,
        sum(fechamentos) filter (where mes > fim - interval 12 month) as baixas_12m,
        sum(fechamentos) filter (where mes <= fim - interval 12 month) as baixas_12m_anteriores
    from radar.aberturas_fechamentos, limites
    where uf like '${inputs.uf.value}'
      and mes > fim - interval 24 month
      and setor <> 'Não informado'
    group by setor
)
select *, baixas_12m / nullif(baixas_12m_anteriores, 0) - 1 as variacao
from base
where baixas_12m_anteriores >= 1000  -- evita variações enormes sobre bases pequenas
order by variacao desc
```

<DataTable data={baixas_setor} rows=25>
    <Column id=setor title="Setor" />
    <Column id=baixas_12m title="Últimos 12 meses" fmt="#,##0" />
    <Column id=baixas_12m_anteriores title="12 meses anteriores" fmt="#,##0" />
    <Column id=variacao title="Variação" fmt=pct1 contentType=delta downIsGood=true />
</DataTable>
