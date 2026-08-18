# M1-B Minimum Financial Source Stack V1

## Design principle

Use the smallest authoritative source set that gives strong historical coverage, revision/PIT support, machine-readable retrieval, and cross-source reconciliation.

## Primary sources

### 1. FRED / ALFRED

Role: U.S. macroeconomic time series and vintage-aware historical data.

Required capabilities:
- series observations;
- real-time periods;
- vintage dates;
- initial-release versus revised observations;
- deterministic request capture.

Reference capabilities:
- FRED series observations expose `realtime_start`, `realtime_end`, and `vintage_dates` controls.
- ALFRED archives the real-time period in which values were originally released and later revised.

### 2. U.S. Treasury Fiscal Data

Role: Treasury/public-debt and government-finance series used for authoritative reconciliation and source metadata.

Required capabilities:
- machine-readable historical/current data;
- published record date;
- dataset metadata/data dictionary;
- raw payload hashing.

### 3. ECB Data Portal SDMX

Role: official euro-area statistical and FX series.

Required capabilities:
- SDMX REST retrieval;
- explicit series keys;
- reporting-period boundaries;
- `updatedAfter` deltas;
- `includeHistory=true` for historical data versions;
- content-negotiated machine-readable formats.

### 4. SEC EDGAR APIs

Role: authoritative issuer filing/submission and XBRL fundamental data.

Required capabilities:
- filing-history retrieval;
- filing/publication timestamps;
- companyfacts/XBRL observations;
- raw JSON capture and hashing;
- filing-date versus period-end separation for PIT controls.

## Initial five-series validation set

1. FRED DGS10 — U.S. 10-Year Treasury Constant Maturity Rate, daily.
2. Treasury official Treasury yield-curve observations for the closest comparable maturity/date window, used for cross-source reconciliation with DGS10 where definitions permit.
3. ECB EXR USD/EUR daily exchange rate series.
4. FRED DEXUSEU — U.S. Dollar to Euro exchange-rate series, used for cross-source reconciliation with ECB where definitions/quotation conventions permit.
5. FRED UNRATE — U.S. civilian unemployment rate, monthly.

## Important comparison rule

Cross-source equality MUST NOT be assumed merely because two labels look similar. The contract MUST compare definition, unit, frequency, observation timestamp, quotation convention, and source availability timestamp before numerical reconciliation.

## PIT rule

For every observation, distinguish:
- observation date;
- source publication/availability date;
- retrieval timestamp;
- later revision/vintage where available.

A value may be used in a historical replay only when its availability timestamp is on or before the replay cutoff.

## First implementation target

Implement one generic ingestion record path that can ingest the five validation series without source-specific fields leaking into the canonical provenance schema.

## Evidence requirement

Each ingested series MUST produce:
- raw snapshot hash;
- normalized record hash;
- provenance record;
- PIT availability evidence;
- deterministic replay result;
- reconciliation result where a comparator source exists.

## Constraints

No backtest, OOS analysis, optimization, Monte Carlo, OPRO promotion, or GEPA implementation before M1-B GREEN.
