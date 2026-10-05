"""Lê os ZIPs do TSE e gera uma base única e enxuta:
ano x turno x UF x município x faixa etária harmonizada.

Os arquivos do TSE são grandes (gênero, escolaridade, estado civil, zona...),
então a leitura é feita em blocos e agregada logo em seguida.

Uso:
    python -m src.consolidate
"""
import re
import zipfile

import pandas as pd

from src.config import ALIASES, DATA_PROCESSED, DATA_RAW, FAIXAS

CHUNK = 500_000


def faixa_harmonizada(rotulo: str) -> str:
    """Converte o rótulo do TSE ('21 a 24 anos', '70 anos', '100 anos ou mais',
    'Inválido'...) na faixa harmonizada, usando o primeiro número do rótulo."""
    if not isinstance(rotulo, str):
        return "Não informado"
    m = re.search(r"\d+", rotulo)
    if not m:
        return "Não informado"
    idade = int(m.group())
    if "superior" in rotulo.lower():  # rótulo antigo: "Superior a 79 anos" = 80+
        idade += 1
    if idade < 16:
        return "Não informado"
    faixa = FAIXAS[0][1]
    for limite, nome in FAIXAS:
        if idade >= limite:
            faixa = nome
    return faixa


def _escolher_csvs(zf: zipfile.ZipFile) -> list[str]:
    """Usa o arquivo nacional (_BRASIL) se existir; senão, todos os arquivos por UF.
    Evita contar o país duas vezes."""
    csvs = [n for n in zf.namelist() if n.lower().endswith((".csv", ".txt"))]
    nacional = [n for n in csvs if "BRASIL" in n.upper()]
    return nacional or csvs


def _mapa_colunas(colunas: list[str]) -> dict[str, str]:
    mapa = {}
    for padrao, opcoes in ALIASES.items():
        for op in opcoes:
            if op in colunas:
                mapa[op] = padrao
                break
    faltando = set(ALIASES) - set(mapa.values())
    if faltando:
        raise ValueError(f"Colunas não encontradas: {faltando}. Colunas do arquivo: {colunas}")
    return mapa


def ler_zip(caminho) -> pd.DataFrame:
    partes = []
    with zipfile.ZipFile(caminho) as zf:
        for nome in _escolher_csvs(zf):
            with zf.open(nome) as f:
                cab = pd.read_csv(f, sep=";", encoding="latin-1", nrows=0).columns.tolist()
            mapa = _mapa_colunas(cab)
            with zf.open(nome) as f:
                leitor = pd.read_csv(
                    f, sep=";", encoding="latin-1", usecols=list(mapa),
                    dtype=str, chunksize=CHUNK,
                )
                for bloco in leitor:
                    bloco = bloco.rename(columns=mapa)
                    for c in ("aptos", "comparecimento", "abstencao"):
                        bloco[c] = pd.to_numeric(bloco[c], errors="coerce").fillna(0).astype("int64")
                    bloco["faixa"] = bloco["faixa_tse"].map(faixa_harmonizada)
                    agg = bloco.groupby(
                        ["ano", "turno", "uf", "cd_municipio", "nm_municipio", "faixa"], as_index=False
                    )[["aptos", "comparecimento", "abstencao"]].sum()
                    partes.append(agg)

    df = pd.concat(partes, ignore_index=True)
    df = df.groupby(
        ["ano", "turno", "uf", "cd_municipio", "nm_municipio", "faixa"], as_index=False
    )[["aptos", "comparecimento", "abstencao"]].sum()
    df["ano"] = df["ano"].astype(int)
    df["turno"] = df["turno"].astype(int)
    df["exterior"] = df["uf"].eq("ZZ")
    return df


def main() -> None:
    zips = sorted(DATA_RAW.glob("perfil_comparecimento_abstencao_*.zip"))
    if not zips:
        raise SystemExit("Nenhum ZIP em data/raw. Rode antes: python -m src.download")

    bases = []
    for z in zips:
        print(f"Lendo {z.name} ...")
        df = ler_zip(z)
        print(f"  {len(df):,} linhas | anos {sorted(df['ano'].unique())}")
        bases.append(df)

    base = pd.concat(bases, ignore_index=True)
    destino = salvar_base(base)
    print(f"\nBase consolidada: {destino} ({len(base):,} linhas)")


def salvar_base(base: pd.DataFrame):
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    try:
        destino = DATA_PROCESSED / "comparecimento_municipio_faixa.parquet"
        base.to_parquet(destino, index=False)
    except ImportError:  # sem pyarrow: cai para CSV compactado
        destino = DATA_PROCESSED / "comparecimento_municipio_faixa.csv.gz"
        base.to_csv(destino, index=False)
    return destino


def carregar_base() -> pd.DataFrame:
    pq = DATA_PROCESSED / "comparecimento_municipio_faixa.parquet"
    if pq.exists():
        return pd.read_parquet(pq)
    csv = DATA_PROCESSED / "comparecimento_municipio_faixa.csv.gz"
    if csv.exists():
        return pd.read_csv(csv, dtype={"cd_municipio": str})
    raise SystemExit("Base não encontrada. Rode antes: python -m src.consolidate")


if __name__ == "__main__":
    main()
