"""Configurações centrais do projeto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

# Arquivo "Comparecimento e Abstenção" do Portal de Dados Abertos do TSE
TSE_URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "perfil_comparecimento_abstencao/perfil_comparecimento_abstencao_{ano}.zip"
)

# Eleições gerais (presidente) — foco do projeto.
# 2026 entra quando o TSE publicar o arquivo detalhado.
ANOS_GERAIS = [2006, 2010, 2014, 2018, 2022, 2026]

# Abstenção oficial do 1º turno (eleições gerais), usada só para checar o pipeline.
# Fontes: TSE / imprensa. Tolerância de 0,3 p.p. por diferenças de recorte.
ABSTENCAO_OFICIAL_1T = {
    2006: 16.75,
    2010: 18.12,
    2014: 19.39,
    2018: 20.33,
    2022: 20.95,
    2026: 21.08,
}

# Faixas etárias harmonizadas (limite inferior -> rótulo).
# O TSE muda os rótulos ao longo dos anos; tudo é mapeado para estas faixas.
FAIXAS = [
    (16, "16-17"),
    (18, "18-24"),
    (25, "25-34"),
    (35, "35-44"),
    (45, "45-59"),
    (60, "60-69"),
    (70, "70-79"),
    (80, "80+"),
]

# Faixas em que o voto é facultativo no Brasil
FAIXAS_FACULTATIVAS = {"16-17", "70-79", "80+"}

# Nomes de colunas aceitos (o layout do TSE varia entre anos)
ALIASES = {
    "ano": ["ANO_ELEICAO"],
    "turno": ["NR_TURNO", "NUM_TURNO"],
    "uf": ["SG_UF"],
    "cd_municipio": ["CD_MUNICIPIO", "COD_MUNICIPIO_TSE"],
    "nm_municipio": ["NM_MUNICIPIO", "NOME_MUNICIPIO"],
    "faixa_tse": ["DS_FAIXA_ETARIA", "DESCRICAO_FAIXA_ETARIA"],
    "aptos": ["QT_APTOS", "QTD_APTOS"],
    "comparecimento": ["QT_COMPARECIMENTO", "QTD_COMPARECIMENTO"],
    "abstencao": ["QT_ABSTENCAO", "QTD_ABSTENCAO"],
}
