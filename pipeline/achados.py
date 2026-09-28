"""Calcula os números-manchete a partir da camada gold (para o README e os posts).

Uso: python -m pipeline.achados [--uf SP]
"""
from __future__ import annotations

import argparse

import duckdb

from pipeline.config import GOLD_DIR


def _tabela(nome: str) -> str:
    return f"read_csv_auto('{(GOLD_DIR / f'gold_{nome}.csv').as_posix()}')"


def _br(n: float, casas: int = 0) -> str:
    return f"{n:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _var(atual: float, anterior: float) -> str:
    return f"{atual / anterior - 1:+.1%}" if anterior else "n/d"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uf", default="%", help="filtra uma UF (padrão: Brasil)")
    uf = p.parse_args().uf
    con = duckdb.connect()
    af = _tabela("aberturas_fechamentos")

    fim = con.sql(f"select max(mes) from {af}").fetchone()[0]
    print(f"Último mês completo: {fim:%m/%Y} | recorte: {'Brasil' if uf == '%' else uf}\n")

    doze = f"mes > date '{fim}' - interval 12 month"
    anteriores = f"mes <= date '{fim}' - interval 12 month and mes > date '{fim}' - interval 24 month"
    a, f, vol, ina, omi, a0, f0, ina0 = con.sql(f"""
        select sum(aberturas) filter (where {doze}), sum(fechamentos) filter (where {doze}),
               sum(fechamentos_voluntarios) filter (where {doze}),
               sum(inaptidoes) filter (where {doze}), sum(inaptidoes_por_omissao) filter (where {doze}),
               sum(aberturas) filter (where {anteriores}), sum(fechamentos) filter (where {anteriores}),
               sum(inaptidoes) filter (where {anteriores})
        from {af} where uf like '{uf}'
    """).fetchone()
    print("== Últimos 12 meses")
    print(f"Aberturas: {_br(a)} ({_var(a, a0)} vs. 12 meses anteriores)")
    print(f"Fechamentos (baixas): {_br(f)} ({_var(f, f0)}); registradas como voluntárias: {vol / f:.1%}")
    pct_omissao = omi / ina if ina else 0
    print(f"Inaptidões: {_br(ina)} ({_var(ina, ina0)}); por omissão de declarações: {pct_omissao:.1%}")

    print("\n== Inaptidões por mês (últimos 24 meses)")
    for mes, n in con.sql(f"""
        select mes, sum(inaptidoes) from {af}
        where uf like '{uf}' and mes > date '{fim}' - interval 24 month
        group by mes order by mes
    """).fetchall():
        print(f"  {mes:%m/%Y}: {_br(n)}")

    print("\n== Setores com maior alta de fechamentos (12m vs. 12m anteriores, mín. 1.000)")
    for setor, atual, antes, var in con.sql(f"""
        select setor,
               sum(fechamentos) filter (where {doze}) as atual,
               sum(fechamentos) filter (where {anteriores}) as antes,
               atual / antes - 1 as var
        from {af} where uf like '{uf}' and setor <> 'Não informado'
        group by setor having antes >= 1000 order by var desc limit 5
    """).fetchall():
        print(f"  {setor}: {_br(antes)} -> {_br(atual)} ({var:+.1%})")

    print("\n== Sobrevivência (coortes dos últimos 10 anos)")
    print("  (sem baixa | sem baixa e sem inaptidão)")
    for anos, perfil, taxa, ativas in con.sql(f"""
        select anos, perfil, sum(sobreviventes) / sum(empresas_avaliadas),
               sum(sobreviventes_ativas) / sum(empresas_avaliadas)
        from {_tabela('sobrevivencia')}
        where uf like '{uf}' and ano_abertura >= year(date '{fim}') - 10
        group by all order by anos, perfil
    """).fetchall():
        print(f"  {anos:>2} anos | {perfil:<6}: {taxa:.1%} | {ativas:.1%}")

    print("\n== Destino de quem saiu do MEI (últimos 3 anos)")
    for destino, pct in con.sql(f"""
        select destino, sum(empresas) / sum(sum(empresas)) over () as pct
        from {_tabela('migracao_mei')}
        where uf like '{uf}' and ano_saida >= year(date '{fim}') - 2
        group by destino order by pct desc
    """).fetchall():
        print(f"  {destino}: {pct:.1%}")

    alfa = con.sql(f"select sum(cnpjs_alfanumericos) from {_tabela('retrato_uf')}").fetchone()[0]
    print(f"\nCNPJs alfanuméricos já emitidos (desde jul/2026): {_br(alfa)}")


if __name__ == "__main__":
    main()
