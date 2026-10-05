"""Baixa os arquivos de comparecimento e abstenção do TSE.

Uso:
    python -m src.download                 # todos os anos de config.ANOS_GERAIS
    python -m src.download --anos 2018 2022
"""
import argparse
import sys

import requests
from tqdm import tqdm

from src.config import ANOS_GERAIS, DATA_RAW, TSE_URL


def baixar(ano: int, forcar: bool = False) -> bool:
    destino = DATA_RAW / f"perfil_comparecimento_abstencao_{ano}.zip"
    if destino.exists() and not forcar:
        print(f"[{ano}] já existe, pulando ({destino.name})")
        return True

    url = TSE_URL.format(ano=ano)
    try:
        resp = requests.get(url, stream=True, timeout=60)
    except requests.RequestException as e:
        print(f"[{ano}] erro de conexão: {e}")
        return False

    if resp.status_code != 200:
        print(f"[{ano}] não disponível (HTTP {resp.status_code}) — {url}")
        return False

    total = int(resp.headers.get("content-length", 0))
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".part")
    with open(tmp, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=str(ano)) as bar:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            f.write(chunk)
            bar.update(len(chunk))
    tmp.rename(destino)
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--anos", nargs="+", type=int, default=ANOS_GERAIS)
    p.add_argument("--forcar", action="store_true", help="baixa de novo mesmo se já existir")
    args = p.parse_args()

    ok = [a for a in args.anos if baixar(a, args.forcar)]
    faltando = sorted(set(args.anos) - set(ok))
    print(f"\nBaixados/presentes: {ok}")
    if faltando:
        print(f"Indisponíveis: {faltando} (o pipeline segue sem eles)")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
