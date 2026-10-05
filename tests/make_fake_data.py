"""Gera ZIPs sintéticos no layout do TSE para testar o pipeline sem internet.

Cenário plantado: a taxa de abstenção de cada faixa etária é IGUAL em todos os anos;
só a estrutura etária envelhece. Logo, a decomposição deve atribuir ~100% da
variação ao efeito composição. Os rótulos de faixa mudam entre anos de propósito.

Uso:
    python -m tests.make_fake_data <pasta_destino>
"""
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# (rótulo antigo, rótulo novo, idade de referência, taxa de abstenção fixa)
FAIXAS = [
    ("16 anos", "16 anos", 16, 0.45), ("17 anos", "17 anos", 17, 0.40),
    ("18 a 20 anos", "18 anos", 18, 0.20), ("21 a 24 anos", "21 a 24 anos", 21, 0.19),
    ("25 a 34 anos", "25 a 29 anos", 25, 0.17), ("35 a 44 anos", "35 a 39 anos", 35, 0.13),
    ("45 a 59 anos", "45 a 49 anos", 45, 0.11), ("60 a 69 anos", "60 a 64 anos", 60, 0.12),
    ("70 a 79 anos", "70 anos", 70, 0.35), ("Superior a 79 anos", "100 anos ou mais", 80, 0.75),
    ("Inválido", "Inválido", None, 0.50),
]
PESO_BASE = np.array([.01, .01, .07, .09, .22, .20, .22, .10, .055, .015, .01])
ENVELHECER = np.array([0, 0, -.004, -.004, -.006, -.002, .002, .006, .006, .002, 0])


def gerar(ano: int, i: int, rng) -> pd.DataFrame:
    pesos = PESO_BASE + i * ENVELHECER
    pesos = pesos / pesos.sum()
    linhas = []
    for uf, mun, nome in [("RS", "88013", "PORTO ALEGRE"), ("SP", "71072", "SÃO PAULO"), ("ZZ", "99999", "EXTERIOR")]:
        tam = 900_000 if uf != "ZZ" else 40_000
        for (velho, novo, _, taxa), w in zip(FAIXAS, pesos):
            for genero in ("MASCULINO", "FEMININO"):
                aptos = int(tam * w / 2)
                t = 0.6 if uf == "ZZ" else taxa
                abst = int(round(aptos * t))
                linhas.append({
                    "DT_GERACAO": "01/01/2026", "ANO_ELEICAO": ano, "NR_TURNO": 1, "SG_UF": uf,
                    "CD_MUNICIPIO": mun, "NM_MUNICIPIO": nome, "DS_GENERO": genero,
                    "DS_FAIXA_ETARIA": velho if ano < 2016 else novo,
                    "QT_APTOS": aptos, "QT_COMPARECIMENTO": aptos - abst, "QT_ABSTENCAO": abst,
                })
    return pd.DataFrame(linhas)


def main(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    for i, ano in enumerate([2010, 2014, 2018, 2022]):
        df = gerar(ano, i, rng)
        with zipfile.ZipFile(dest / f"perfil_comparecimento_abstencao_{ano}.zip", "w") as zf:
            for uf, parte in df.groupby("SG_UF"):
                buf = io.StringIO()
                parte.to_csv(buf, sep=";", index=False)
                zf.writestr(f"perfil_comparecimento_abstencao_{ano}_{uf}.csv", buf.getvalue().encode("latin-1"))
    print(f"ZIPs sintéticos em {dest}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
