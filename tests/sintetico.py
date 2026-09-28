"""Gera zips sintéticos no mesmo formato dos arquivos da Receita.

Latin-1, ';' como separador, tudo entre aspas, sem cabeçalho, com as "pegadinhas"
reais da base: acentos, quebra de linha dentro de campo e CNPJ alfanumérico.
"""
from __future__ import annotations

import random
import zipfile
from datetime import date, timedelta
from pathlib import Path

PESOS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
PESOS_2 = [6] + PESOS_1


def dv_cnpj(base12: str) -> str:
    """Dígitos verificadores de um CNPJ (numérico ou alfanumérico)."""
    valores = [ord(c) - 48 for c in base12]
    digitos = ""
    for pesos in (PESOS_1, PESOS_2):
        resto = sum(v * p for v, p in zip(valores, pesos, strict=True)) % 11
        dv = 0 if resto < 2 else 11 - resto
        valores.append(dv)
        digitos += str(dv)
    return digitos


def _linha(campos: list[object]) -> str:
    return ";".join(f'"{c}"' for c in campos) + "\n"


def _zip(pasta: Path, nome_zip: str, linhas: list[str]) -> None:
    conteudo = "".join(linhas).encode("latin-1")
    with zipfile.ZipFile(pasta / nome_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"K3241.K03200Y0.D60912.{nome_zip[:8].upper()}", conteudo)


def _data(d: date | None) -> str:
    return d.strftime("%Y%m%d") if d else "00000000"


def gerar(pasta: Path, n_empresas: int = 300, semente: int = 42) -> dict[str, int]:
    """Cria os zips em `pasta`. Retorna {nome_zip: nº de registros}."""
    rnd = random.Random(semente)
    pasta.mkdir(parents=True, exist_ok=True)
    ufs = ["SP", "RJ", "MG", "BA", "RS", "PE", "PR", "CE", "AM", "GO"]
    cnaes = ["4781400", "5611201", "6201501", "4120400", "8599604", "9602501"]

    empresas, estabelecimentos, simples = [], [], []
    for i in range(n_empresas):
        basico = f"{i + 10_000_000:08d}"
        if i == 0:
            basico = "12ABC345"  # CNPJ alfanumérico (IN RFB 2.229/2024)
        ordem = "0001" if i else "01DE"
        cnpj_dv = dv_cnpj(basico + ordem)
        inicio = date(2012, 1, 1) + timedelta(days=rnd.randint(0, 5200))
        situacao, data_sit, motivo = "02", inicio, "00"
        if rnd.random() < 0.4:
            situacao = "08"
            data_sit = inicio + timedelta(days=rnd.randint(30, 2500))
            motivo = rnd.choice(["01", "54", "63", "71", "02"])
        nome_fantasia = "PADARIA SÃO JOÃO" if i % 7 else "LOJA\nCOM QUEBRA"  # quebra de linha real
        estabelecimentos.append(_linha([
            basico, ordem, cnpj_dv, "1", nome_fantasia, situacao, _data(data_sit), motivo, "", "",
            _data(inicio), rnd.choice(cnaes), "", "RUA", "DAS ACÁCIAS", "10", "", "CENTRO",
            "01001000", rnd.choice(ufs), "7107", "11", "999999999", "", "", "", "", "", "", "",
        ]))
        empresas.append(_linha([basico, "EMPRESA TESTE", "2135", "50", "1000,00", "01", ""]))
        eh_mei = rnd.random() < 0.6
        saiu = eh_mei and rnd.random() < 0.3
        simples.append(_linha([
            basico, "S" if eh_mei or rnd.random() < 0.5 else "N", _data(inicio), "00000000",
            "N" if saiu or not eh_mei else "S", _data(inicio) if eh_mei else "00000000",
            _data(inicio + timedelta(days=700)) if saiu else "00000000",
        ]))

    # CNPJ de campanha eleitoral: aberto e baixado em 31/12 (não pode contar como empresa).
    basico = "99999999"
    estabelecimentos.append(_linha([
        basico, "0001", dv_cnpj(basico + "0001"), "1", "ELEICAO 2024 FULANO", "08", "20241231", "01", "", "",
        "20240815", "9492800", "", "", "", "", "", "", "", "SP", "7107", "", "", "", "", "", "", "", "", "",
    ]))
    empresas.append(_linha([basico, "ELEICAO 2024 FULANO", "4090", "51", "0,00", "05", ""]))

    # Raiz duplicada com registro vazio, como acontece na base real (set/2026).
    empresas.append(_linha([f"{10_000_001:08d}", "", "0000", "00", "0,00", "", ""]))

    arquivos = {
        "Estabelecimentos0.zip": estabelecimentos,
        "Empresas0.zip": empresas,
        "Simples.zip": simples,
        "Cnaes.zip": [_linha([c, f"ATIVIDADE {c}"]) for c in [*cnaes, "9492800"]],
        "Motivos.zip": [_linha([m, d]) for m, d in [
            ("00", "SEM MOTIVO"), ("01", "EXTINCAO POR ENCERRAMENTO LIQUIDACAO VOLUNTARIA"),
            ("02", "INCORPORACAO"), ("54", "EXTINCAO - TRATAMENTO DIFERENCIADO DADO AS ME E EPP"),
            ("63", "OMISSAO DE DECLARACOES"), ("71", "INAPTIDAO (LEI 11.941/2009 ART.54)"),
        ]],
        "Municipios.zip": [_linha(["7107", "SAO PAULO"])],
        "Naturezas.zip": [_linha(["2135", "EMPRESÁRIO (INDIVIDUAL)"])],
        "Paises.zip": [_linha(["105", "BRASIL"])],
        "Qualificacoes.zip": [_linha(["50", "EMPRESÁRIO"])],
    }
    for nome, linhas in arquivos.items():
        _zip(pasta, nome, linhas)
    return {nome: len(linhas) for nome, linhas in arquivos.items()}
