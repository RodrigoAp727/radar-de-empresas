"""Descoberta e download dos arquivos mensais do CNPJ.

Desde 2025 a Receita publica os dados num compartilhamento público do Nextcloud
(SERPRO+). O acesso é por WebDAV: usuário = token do compartilhamento, senha vazia.
"""
from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

import requests

from pipeline.config import RECEITA_SHARE_TOKEN, RECEITA_WEBDAV_URL

log = logging.getLogger(__name__)

_SESSAO = requests.Session()
_SESSAO.auth = (RECEITA_SHARE_TOKEN, "")
_SESSAO.headers["User-Agent"] = "radar-de-empresas (dados abertos CNPJ)"
_CHUNK = 8 * 1024 * 1024
_NS = {"d": "DAV:"}


def _com_retry(metodo: str, url: str, tentativas: int = 5, **kwargs) -> requests.Response:
    """Requisição com retry exponencial: o servidor da Receita oscila bastante."""
    for n in range(1, tentativas + 1):
        try:
            resp = _SESSAO.request(metodo, url, timeout=(30, 300), **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as erro:
            if n == tentativas:
                raise
            espera = 2 ** n * 5
            log.warning("Falha em %s (%s). Nova tentativa em %ss", url, erro, espera)
            time.sleep(espera)
    raise AssertionError("inalcançável")


def _listar(caminho: str = "") -> dict[str, int]:
    """PROPFIND de um nível: {nome: tamanho em bytes} (pastas vêm com tamanho 0)."""
    resp = _com_retry("PROPFIND", f"{RECEITA_WEBDAV_URL}{caminho}", headers={"Depth": "1"})
    itens: dict[str, int] = {}
    for r in ET.fromstring(resp.content).findall("d:response", _NS):
        href = unquote(r.findtext("d:href", "", _NS)).rstrip("/")
        nome = href.rsplit("/", 1)[-1]
        tamanho = r.findtext(".//d:getcontentlength", "0", _NS)
        itens[nome] = int(tamanho or 0)
    return itens


def ultima_referencia() -> str:
    refs = sorted(n for n in _listar() if re.fullmatch(r"\d{4}-\d{2}", n))
    if not refs:
        raise RuntimeError(
            f"Nenhuma pasta AAAA-MM em {RECEITA_WEBDAV_URL}. A Receita pode ter mudado o "
            "compartilhamento: ajuste RADAR_SHARE_TOKEN / RADAR_WEBDAV_URL."
        )
    return refs[-1]


def listar_zips(referencia: str) -> dict[str, int]:
    return {n: t for n, t in _listar(f"{referencia}/").items() if n.lower().endswith(".zip")}


def baixar(referencia: str, nome_zip: str, tamanho: int, destino_dir: Path) -> Path:
    """Baixa um zip em streaming. Pula se já existir com o mesmo tamanho."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / nome_zip
    if destino.exists() and destino.stat().st_size == tamanho:
        log.info("%s já baixado", nome_zip)
        return destino

    parcial = destino.with_suffix(".part")
    inicio = time.monotonic()
    with _com_retry("GET", f"{RECEITA_WEBDAV_URL}{referencia}/{nome_zip}", stream=True) as resp, \
            open(parcial, "wb") as f:
        for bloco in resp.iter_content(_CHUNK):
            f.write(bloco)

    if tamanho and parcial.stat().st_size != tamanho:
        raise OSError(f"{nome_zip}: baixados {parcial.stat().st_size} de {tamanho} bytes")
    parcial.replace(destino)
    log.info("%s: %.0f MB em %.0fs", nome_zip, tamanho / 1e6, time.monotonic() - inicio)
    return destino
