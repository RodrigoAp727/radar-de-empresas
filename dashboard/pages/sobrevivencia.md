---
title: Quanto tempo uma empresa sobrevive
---

Das empresas abertas em um ano, quantas continuavam de pé 1, 2, 3, 5 e 10 anos depois.
Só entram na conta as empresas que já tiveram tempo de completar cada prazo.

Há duas formas de medir, e a diferença entre elas é grande:

- **Sem baixa**: o CNPJ não foi encerrado. É a definição cadastral, e a mais otimista.
- **Sem baixa e sem inaptidão**: também não foi declarada inapta pela Receita. Uma empresa inapta
  por omissão de declarações, em geral, já parou de funcionar. É a medida mais realista.

```sql ufs
select distinct uf from radar.sobrevivencia
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

<ButtonGroup name=medida title="Medida">
    <ButtonGroupItem valueLabel="Sem baixa e sem inaptidão" value="sobreviventes_ativas" default />
    <ButtonGroupItem valueLabel="Sem baixa" value="sobreviventes" />
</ButtonGroup>

```sql filtrado
select *, ${inputs.medida} as vivas
from radar.sobrevivencia
where uf like '${inputs.uf.value}'
  and perfil like '${inputs.perfil}'
```

```sql curva
select
    cast(anos as integer) || (case when anos = 1 then ' ano' else ' anos' end) as prazo,
    anos,
    sum(vivas) / sum(empresas_avaliadas) as taxa
from ${filtrado}
where ano_abertura >= (select max(ano_abertura) from ${filtrado}) - 10
group by all
order by anos
```

<BarChart
    data={curva}
    x=prazo
    y=taxa
    yFmt=pct0
    sort=false
    colorPalette={['#2a78d6']}
    title="Empresas ainda de pé depois de..."
    subtitle="Coortes dos últimos 10 anos"
/>

## Sobrevivência em 3 anos, por setor

```sql por_setor
select
    setor,
    sum(vivas) / sum(empresas_avaliadas) as taxa_3_anos,
    sum(empresas_avaliadas) as empresas_avaliadas
from ${filtrado}
where anos = 3
  and ano_abertura >= (select max(ano_abertura) from ${filtrado}) - 5
  and setor <> 'Não informado'
group by setor
having sum(empresas_avaliadas) >= 100
order by taxa_3_anos desc
```

<BarChart
    data={por_setor}
    x=setor
    y=taxa_3_anos
    swapXY=true
    yFmt=pct0
    sort=false
    colorPalette={['#2a78d6']}
    chartAreaHeight=520
    subtitle="Empresas abertas nos últimos 5 anos com 3 anos completos"
/>

## A sobrevivência mudou ao longo do tempo?

```sql por_coorte
select
    cast(ano_abertura as integer)::varchar as ano_abertura,
    sum(vivas) filter (where anos = 2) / sum(empresas_avaliadas) filter (where anos = 2) as "2 anos"
from ${filtrado}
group by ano_abertura
having sum(empresas_avaliadas) filter (where anos = 2) > 0
order by ano_abertura
```

<LineChart
    data={por_coorte}
    x=ano_abertura
    y="2 anos"
    yFmt=pct0
    colorPalette={['#2a78d6']}
    title="Empresas ainda de pé 2 anos depois, por ano de abertura"
/>
