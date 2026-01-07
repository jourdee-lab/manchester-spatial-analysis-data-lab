# 1981 Census – SAS 04 (Country of Birth)

This directory contains the **1981 Census Small Area Statistics (SAS) Table 04** for Great Britain, providing counts of usual residents by **country of birth** at small‑area level.[web:23][file:8]

## Source

- Original data: UK Data Service – *1981 Census: Small Area Statistics* (CASWEB archive).[web:23]
- Table: **SAS 04 – Country of birth**
- Geography: Small areas / zones (e.g. `0C`, `0D`, `0E`) covering Great Britain.[web:19][web:23]

## File Structure

The full SAS 04 table is split into five CSV parts:

- `81sas04ews_0.csv`
- `81sas04ews_1.csv`
- `81sas04ews_2.csv`
- `81sas04ews_3.csv`
- `81sas04ews_4.csv`

Each file has the same column layout:

- `zoneid` – small‑area identifier
- `81sas040320`–`81sas040379` – numeric columns corresponding to SAS 04 variables.[file:8]  
  Variable definitions are stored in `1981_variable_lookup.csv` (see section below).[file:8]

To reconstruct the full table, vertically concatenate all five files.

## Key Variables for This Project

From the 1981 variable lookup, SAS 04 is coded as `S04*****`.[file:8] Important columns:

- `81sas040320` – **TOTAL: country of birth, all persons**
- `81sas040323`–`81sas040331` – England, Scotland, Wales.[file:8]
- `81sas040335`–`81sas040337` – Irish Republic.[file:8]
- `81sas040338`–`81sas040343` – Old and New Commonwealth.[file:8]
- `81sas040353`–`81sas040355` – India.[file:8]
- `81sas040356`–`81sas040358` – Bangladesh.[file:8]
- `81sas040359`–`81sas040361` – **Far East (total / male / female)** – used here as a proxy for Chinese‑
