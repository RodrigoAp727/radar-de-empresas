"""Configuração central: caminhos, URL da Receita e layout dos arquivos do CNPJ.

O layout segue o dicionário de dados oficial da Receita Federal
(arquivos sem cabeçalho, separados por ';', codificação latin-1).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("RADAR_DATA_DIR", RAIZ / "data")).resolve()
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
GOLD_DIR = DATA_DIR / "gold"
TMP_DIR = DATA_DIR / "tmp"
DUCKDB_PATH = DATA_DIR / "radar.duckdb"
DBT_DIR = RAIZ / "dbt"
DASHBOARD_GOLD_DB = RAIZ / "dashboard" / "sources" / "radar" / "radar_gold.duckdb"

# Compartilhamento público da Receita no Nextcloud (SERPRO+), acessado por WebDAV.
# Página para humanos: https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9
RECEITA_SHARE_TOKEN = os.environ.get("RADAR_SHARE_TOKEN", "YggdBLfdninEJX9")
RECEITA_WEBDAV_URL = os.environ.get(
    "RADAR_WEBDAV_URL", "https://arquivos.receitafederal.gov.br/public.php/webdav/"
)

# Colunas na ordem exata do layout da Receita.
LAYOUTS: dict[str, list[str]] = {
    "empresas": [
        "cnpj_basico", "razao_social", "natureza_juridica", "qualificacao_responsavel",
        "capital_social", "porte_empresa", "ente_federativo_responsavel",
    ],
    "estabelecimentos": [
        "cnpj_basico", "cnpj_ordem", "cnpj_dv", "identificador_matriz_filial", "nome_fantasia",
        "situacao_cadastral", "data_situacao_cadastral", "motivo_situacao_cadastral",
        "nome_cidade_exterior", "pais", "data_inicio_atividade", "cnae_fiscal_principal",
        "cnae_fiscal_secundaria", "tipo_logradouro", "logradouro", "numero", "complemento",
        "bairro", "cep", "uf", "municipio", "ddd_1", "telefone_1", "ddd_2", "telefone_2",
        "ddd_fax", "fax", "correio_eletronico", "situacao_especial", "data_situacao_especial",
    ],
    "socios": [
        "cnpj_basico", "identificador_socio", "nome_socio", "cnpj_cpf_socio", "qualificacao_socio",
        "data_entrada_sociedade", "pais", "representante_legal", "nome_representante",
        "qualificacao_representante", "faixa_etaria",
    ],
    "simples": [
        "cnpj_basico", "opcao_simples", "data_opcao_simples", "data_exclusao_simples",
        "opcao_mei", "data_opcao_mei", "data_exclusao_mei",
    ],
    "cnaes": ["codigo", "descricao"],
    "motivos": ["codigo", "descricao"],
    "municipios": ["codigo", "descricao"],
    "naturezas": ["codigo", "descricao"],
    "paises": ["codigo", "descricao"],
    "qualificacoes": ["codigo", "descricao"],
}

# Sócios não entram nas análises (e concentram dados pessoais): fora por padrão.
TABELAS_PADRAO = [t for t in LAYOUTS if t != "socios"]

PARTICIONADAS = {"empresas", "estabelecimentos", "socios"}
# No modo amostra, só esta parte de cada tabela particionada (a parte 0 é ~6x maior que as outras).
PARTE_AMOSTRA = 1

_PARTICIONADAS = re.compile(r"^(Empresas|Estabelecimentos|Socios)(\d+)\.zip$", re.IGNORECASE)


def tabela_do_arquivo(nome_zip: str) -> tuple[str, int] | None:
    """'Estabelecimentos3.zip' -> ('estabelecimentos', 3); 'Cnaes.zip' -> ('cnaes', 0)."""
    m = _PARTICIONADAS.match(nome_zip)
    if m:
        return m.group(1).lower(), int(m.group(2))
    base = nome_zip.rsplit(".", 1)[0].lower()
    return (base, 0) if base in LAYOUTS else None
