---
title: Radar de Empresas BR
---

Quantas empresas abrem e fecham no Brasil, em quais setores e em quais estados. Os números vêm da
base pública do CNPJ da Receita Federal e são atualizados todo mês por um
[pipeline automático](https://github.com/RodrigoAp727/radar-de-empresas).

```sql referencia
select max(referencia) as referencia from radar.retrato_uf
```

<small>Base da Receita de <Value data={referencia} column=referencia />. Fechamento = empresa baixada (situação 08); inapta = declarada irregular pela Receita (situação 04). Veja <a href="fechamentos">Baixas e inaptidões</a>.</small>

```sql ufs
select distinct uf from radar.aberturas_fechamentos
where uf is not null and uf <> 'EX'
order by uf
```

<Dropdown name=uf data={ufs} value=uf title="Estado" defaultValue="%">
    <DropdownOption value="%" valueLabel="Brasil" />
</Dropdown>

<ButtonGroup name=perfil title="Perfil">
    <ButtonGroupItem valueLabel="Todas" value="%" default />
    <ButtonGroupItem valueLabel="MEI" value="MEI" />
    <ButtonGroupItem valueLabel="Demais" value="Demais" />
</ButtonGroup>

```sql filtrado
select *
from radar.aberturas_fechamentos
where uf like '${inputs.uf.value}'
  and perfil like '${inputs.perfil}'
```

```sql kpis
with limites as (select max(mes) as fim from ${filtrado})
select
    sum(aberturas) filter (where mes > fim - interval 12 month) as aberturas_12m,
    sum(fechamentos) filter (where mes > fim - interval 12 month) as fechamentos_12m,
    sum(aberturas) filter (where mes > fim - interval 12 month)
        / nullif(sum(aberturas) filter (where mes <= fim - interval 12 month and mes > fim - interval 24 month), 0) - 1
        as var_aberturas,
    sum(fechamentos) filter (where mes > fim - interval 12 month)
        / nullif(sum(fechamentos) filter (where mes <= fim - interval 12 month and mes > fim - interval 24 month), 0) - 1
        as var_fechamentos,
    sum(inaptidoes) filter (where mes > fim - interval 12 month) as inaptidoes_12m
from ${filtrado}, limites
```

```sql ativas
select
    sum(empresas_ativas) as empresas_ativas,
    sum(mei_ativos) as mei_ativos
from radar.retrato_uf
where uf like '${inputs.uf.value}'
```

<Grid cols=4>
    <BigValue data={ativas} value=empresas_ativas title="Empresas ativas" fmt="#,##0" />
    <BigValue data={kpis} value=aberturas_12m title="Aberturas (12 meses)" fmt="#,##0"
        comparison=var_aberturas comparisonFmt=pct1 comparisonTitle="vs. 12 meses anteriores" />
    <BigValue data={kpis} value=fechamentos_12m title="Fechamentos (12 meses)" fmt="#,##0"
        comparison=var_fechamentos comparisonFmt=pct1 comparisonTitle="vs. 12 meses anteriores" downIsGood=true />
    <BigValue data={kpis} value=inaptidoes_12m title="Declaradas inaptas (12 meses)" fmt="#,##0" />
</Grid>

## Aberturas e fechamentos por mês

```sql serie
select
    mes,
    sum(aberturas) as "Aberturas",
    sum(fechamentos) as "Fechamentos"
from ${filtrado}
group by mes
order by mes
```

<LineChart
    data={serie}
    x=mes
    y={['Aberturas', 'Fechamentos']}
    yFmt="#,##0"
    colorPalette={['#2a78d6', '#eb6834']}
    chartAreaHeight=280
/>

## Saldo dos últimos 12 meses por setor

Aberturas menos fechamentos. Setores com saldo negativo perderam empresas no período.

```sql saldo_setor
with limites as (select max(mes) as fim from ${filtrado})
select
    setor,
    sum(aberturas) - sum(fechamentos) as saldo,
    sum(aberturas) as aberturas,
    sum(fechamentos) as fechamentos
from ${filtrado}, limites
where mes > fim - interval 12 month
  and setor <> 'Não informado'
group by setor
order by saldo desc
```

<BarChart
    data={saldo_setor}
    x=setor
    y=saldo
    swapXY=true
    yFmt="#,##0"
    colorPalette={['#2a78d6']}
    sort=false
    chartAreaHeight=520
/>

<DataTable data={saldo_setor} rows=25>
    <Column id=setor title="Setor" />
    <Column id=aberturas title="Aberturas" fmt="#,##0" />
    <Column id=fechamentos title="Fechamentos" fmt="#,##0" />
    <Column id=saldo title="Saldo" fmt="#,##0" contentType=delta />
</DataTable>
