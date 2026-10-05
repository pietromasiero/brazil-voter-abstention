# Is Brazil's "record" voter abstention really a record?

> 🇧🇷 *A abstenção recorde de 2026 é efeito do envelhecimento do eleitorado?* — versão em português abaixo.

On October 4, 2026, **21.08%** of Brazil's registered voters skipped the first round of the general election, the highest rate since 1998, and headlines called it a record.

But Brazil's electorate is aging, and **voting is optional for people aged 70+** (and for 16–17 year-olds). If the share of older voters grows, total abstention rises even if *nobody* changes their behavior.

This project separates the two effects using official open data from Brazil's Superior Electoral Court (TSE):

| Question | Method |
|---|---|
| What would abstention be if the electorate had the age structure of an earlier election? | **Direct age standardization** |
| How much of each change comes from *who* the voters are vs. *how* they behave? | **Kitagawa decomposition** (composition vs. rate effect) |
| Where did abstention actually grow, once age is accounted for? | Age-adjusted rates by municipality |

## Pipeline

```
src/download.py      →  data/raw/        TSE "Comparecimento e Abstenção" ZIPs, one per election
src/consolidate.py   →  data/processed/  one tidy table: year × round × state × municipality × age band
src/analysis.py      →  outputs/*.csv    national, by-age, standardized, decomposition, municipal tables
src/charts.py        →  outputs/*.png    charts for the write-up
```

Design choices:

- **Chunked reading + early aggregation**: TSE files break voters down by gender, education, marital status and electoral zone (millions of rows). Only the needed columns are read, in chunks, and aggregated immediately.
- **Harmonized age bands**: TSE age labels change across years (`"Superior a 79 anos"`, `"70 anos"`, `"100 anos ou mais"`…). All are mapped to consistent bands: 16-17, 18-24, 25-34, 35-44, 45-59, 60-69, 70-79, 80+.
- **Schema aliases**: column names that vary between releases are resolved in `config.py`.
- **No double counting**: a national file is used when present; otherwise per-state files are combined.
- **Built-in validation**: national totals are checked against official TSE abstention rates.
- **Voters abroad** (`UF = ZZ`) are flagged and can be included or excluded.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.download             # downloads every available year (≈ a few GB)
python -m src.consolidate
python -m src.analysis             # 1st round; reference age structure = earliest year
python -m src.charts
```

Options: `python -m src.download --anos 2018 2022`, `python -m src.analysis --turno 2 --ano-ref 2010`.

The CSVs in `outputs/` use `;` and `,` decimals, so they open directly in Excel and Power BI (pt-BR locale).

### Testing without internet

`tests/make_fake_data.py` creates synthetic ZIPs in the TSE layout where abstention **within each age band never changes**, only the age structure. The decomposition should attribute ~100% of the change to composition:

```bash
python -m tests.make_fake_data data/raw
python -m src.consolidate && python -m src.analysis
```

## Limitations

- Standardization only controls for **age**. Education, region and registry quality also matter.
- The voter registry includes people who died or moved and are not yet removed. They count as "abstention" and this project cannot separate them out.
- The detailed 2026 file depends on TSE's publication schedule. Until then, 2026 appears only in the headline rate.

## Data

Tribunal Superior Eleitoral — [Portal de Dados Abertos](https://dadosabertos.tse.jus.br/), dataset *Comparecimento e Abstenção* (CC-BY).

---

## 🇧🇷 Resumo em português

Em 2026, a abstenção no 1º turno foi de 21,08%, a maior desde 1998. Mas o eleitorado está envelhecendo, e o voto é facultativo a partir dos 70 anos. Este projeto usa dados abertos do TSE para separar quanto da alta vem da **mudança de idade do eleitorado** e quanto vem de **mudança de comportamento**, com padronização etária e decomposição de Kitagawa, incluindo o recorte por município.
