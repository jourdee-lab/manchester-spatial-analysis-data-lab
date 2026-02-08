# 1991 UK Census Data Structure: Technical Specification for AI Systems

## Overview

The 1991 Census data from the UK Data Service represents a hierarchical, aggregated statistical system designed for privacy-protected population and housing research. Unlike modern microdata systems, the 1991 Census was released primarily as pre-computed aggregate tables at fixed geographic units, with strict confidentiality protocols. This structure requires AI systems to understand the relationships between variable definitions, geographic hierarchies, processing thresholds, and data availability rules.

## 1. Data Collection and Enumeration Structure

### Enumeration Districts (EDs)

The 1991 Census divided Great Britain into approximately 130,000 Enumeration Districts (EDs), the fundamental geographic unit for fieldwork. Each ED was designed to contain a feasible workload for a single enumerator:

- **England and Wales**: Average of 200 households (~400 persons) per ED
- **Scotland**: Slightly smaller EDs, aggregated into Output Areas (OAs) for statistical output rather than using EDs directly

ED boundaries were deliberately constructed to respect administrative divisions (wards, districts, counties) where possible, minimizing cross-boundary fragmentation. They accounted for geographic and demographic factors affecting enumeration difficulty: scattered rural populations, multi-occupied urban buildings, non-English-speaking households, and communal establishment concentrations.

### Questionnaire and Form Structure

The 1991 Census employed three form types:

| Form Type | Use Case | Sample Size |
|-----------|----------|------------|
| **H Form (W in Wales)** | Household enumeration | 100% of households |
| **I Form (Iw in Wales)** | Individual enumeration (communal establishments) | 100% of communal residents |
| **L Form** | Listing form (communal establishments) | 100% of establishments |

Each form contained 25 core questions, plus regional variations (Welsh/Gaelic language in Wales/Scotland; floor level in Scotland only).

## 2. Data Processing Architecture

The 1991 Census employed a two-tier processing strategy that fundamentally shapes data availability:

### 100% Processing (Full Census Questions)

Tick-box and straightforward responses were processed for the entire population:

**Variables in 100% Processing:**
- **Demographic**: Sex, date of birth, marital status, whereabouts on census night, usual residence, country of birth, ethnic group (10 full categories → 4–10 output categories), long-term illness limiting activities
- **Migration**: Usual address 1 year ago (type of move: same address, different address within GB, moved abroad)
- **Housing**: Dwelling type, household space type (multi-occupied), number of rooms, tenure (owner-occupied, council rent, private rent, etc.), amenities (heating, indoor toilet, bath/shower), availability of cars/vans
- **Language**: Welsh and Gaelic language use (6 combinations)
- **Economic**: Economic position and employment status (employed, unemployed, student, retired, etc.)

Processing order: County-by-county (regional in Scotland). The 100% tables were produced first, enabling Local Base Statistics (LBS) and Small Area Statistics (SAS) release within ~6 weeks of census processing.

### 10% Sample Processing (Complex Questions)

Complex open-ended questions requiring manual coding were processed for a 1-in-10 systematic sample:

**Variables in 10% Processing:**
- **Occupation**: Standard Occupational Classification (SOC) with 9 major groups, 22 sub-major groups, 77 minor groups, and 371 unit codes
- **Industry**: Standard Industrial Classification (SIC) with 10 divisions, 60 classes, 222 groups, and 334 activity headings
- **Household Composition**: 21 family unit types and household composition classifications
- **Work**: Hours worked per week (12 bands: <15, 15–20, ..., >60 hours), workplace type (home-based, fixed workplace, mobile), transport to work (12 modes)
- **Qualifications**: Higher qualifications (3 levels) by subject group (10 subjects)
- **Social Class**: Registrar General's Social Class (I–V) derived from occupation; Socio-economic Group (20 groups)

Sample selection: Households were ordered geographically within EDs; every 10th household was selected. Persons in communal establishments were stratified into groups of 50 and one randomly selected. This 10% sample was also the basis for the Samples of Anonymised Records (SARs), providing 31,967 individual records on 10 geographic area files.

The 10% tables became available ~4–5 months after the 100% release.

## 3. Output Data Products: SAS, LBS, and Beyond

### Small Area Statistics (SAS)

**Purpose**: Provide detailed cross-tabulations at the smallest feasible geographic units.

**Coverage**: 
- **England/Wales**: Enumeration District level
- **Scotland**: Output Area level (OA; created by aggregating ED-level postcode data to respect 1981 SAS boundaries)

**Table Count and Structure**: 86 tables with approximately 20,000 cell counts. Tables cross-tabulate population bases (e.g., "residents in households") with 1–3 variables:

| Table Category | Examples | Processing |
|---|---|---|
| **Population Bases** | Table 1: population present, residents, households | 100% |
| **Demographic Breakdown** | Age/sex (5-year groups), marital status | 100% |
| **Migration** | 1-year prior residence by area | 100% |
| **Housing** | Dwelling type, tenure, amenities, cars | 100% |
| **Economic Activity** | Employment status by age/sex | 100% |
| **Occupation/Industry** | SOC/SIC cross-tabs by residence | 10% |
| **Qualifications** | Educational attainment by age | 10% |

**Confidentiality Threshold**: SAS are not released for areas with fewer than 50 usually resident persons and 16 resident households. If an ED/OA falls below these thresholds, its statistics are merged with a contiguous ED/OA, creating "merged" or "imputed" areas marked in output. This process ensures no SAS table reveals information about identifiable individuals or households.

### Local Base Statistics (LBS)

**Purpose**: Provide comprehensive local-area tables at wider geographic units with greater categorical detail.

**Coverage**:
- **England/Wales**: Ward level and aggregations
- **Scotland**: Postcode sector level and aggregations
- Down to district and county levels

**Table Count and Structure**: 99 tables with greater detail than SAS. For example, age is reported in single-year groups rather than 5-year bands, enabling more granular analysis.

**Confidentiality Threshold**: LBS are released only for wards/postcode sectors with ≥1,000 residents and ≥320 households. Below this, they are merged with contiguous areas following ward amalgamation procedures.

**Modification**: Both SAS and LBS counts at ward and ED levels are modified (±1, 0, or +1 added in quasi-random patterns) to prevent indirect disclosure of individuals, except for basic counts (population, households) and establishment counts where modification would impair utility.

### County/Region Reports

First reports produced from 100% processing, followed by detailed county-level tabulations. Available in two parts: Part 1 (100%) and Part 2 (10% sample).

### Topic Reports

Thematic publications covering specific domains:
- Sex, Age, and Marital Status
- Economic Activity and Employment
- Workplace and Transport to Work
- Housing and Availability of Cars
- Household and Family Composition
- Qualified Manpower
- Ethnic Group and Country of Birth
- Migration (Parts 1 and 2)
- Limiting Long-term Illness

Published across 1992–1993 at national and sub-national levels.

## 4. Geographic Hierarchy and Coding

The 1991 Census employed a standardized multi-level geographic framework:

| Level | England/Wales | Scotland | Nesting |
|-------|---|---|---|
| **National** | GB, England, Wales | Scotland | — |
| **Regional** | 8 Standard Regions (e.g., South East includes Outer Metropolitan/Outer South East) | 9 Regions + 3 Island Areas | Region > Country |
| **County/Region** | 55 non-metropolitan + 32 metropolitan counties | 9 regions | County/Region > Region |
| **District** | 403 local authority districts (33 London boroughs) | 53 districts | District > County |
| **Ward** | Civil parishes, wards, communities | Postcode sectors (multiple); electoral divisions in some areas | Ward > District |
| **Small Area** | **Enumeration District (~130k; avg. 200 hh)** | **Output Area (aggregate EDs by postcode)** | ED/OA > Ward |

**Key Geographic Codes**: Areas are identified by hierarchical numeric codes (e.g., ED code embeds county, district, and local code). Scotland uses postcode-based OAs, while England/Wales use ED administrative boundaries. These codes enable cross-linking with postcodes and other geographic datasets, though only within confidentiality constraints.

## 5. Population Bases and Data Definitions

### Population Bases

Census tables are built on specific population bases, critical for AI interpretation:

| Population Base | Definition | Census Night | 1 Year Ago | Use |
|---|---|---|---|---|
| **Persons Present** | All present on census night (21–22 April 1991) | ✓ | — | Preliminary counts, special areas |
| **Residents (topped-up)** | Usually resident + absent residents from wholly absent households | (Residents + Absent) | — | Most SAS/LBS tables (main base) |
| **Residents in Households** | Residents in private households (excludes communal) | ✓ | — | Housing tables |
| **Employed Persons** | Economically active, in employment | ✓ | — | Occupation/industry tables |

**Critical Detail**: Absent households (whole household away on census night) were asked to return forms voluntarily. Non-responders were imputed using similar household records matched on area, number of residents, rooms, and self-contained status. This ensures the "topped-up" resident population includes estimates for non-responders, making 1991 SAS more complete than 1981 (which omitted wholly absent households).

### Variable Classifications

Key variable hierarchies (enabling AI to parse tables):

**Ethnic Group** (100% question, full 10-category hierarchy):
- White British, Irish, Other White
- Mixed (4 types)
- Asian/Asian British (4 types)
- Black/Black British (3 types)
- Chinese
- Other

Output typically collapses to 4–10 categories depending on cell size and geographic level.

**Socio-economic Group (SEG)** (10% question; 20 groups):
1. Employers in agriculture
2. Managers/professionals (self-employed, employees)
3. Intermediate/junior non-manual
4. Foremen/supervisors (manual)
5. Skilled manual workers
...and 15 others, including unemployed and students.

**Household Composition** (10% question; 21 types):
- One-person households (elderly, non-elderly)
- Couples without children
- Couples with dependent/non-dependent children
- Lone parents with children
- Multi-family households
- Others

## 6. Confidentiality, Suppression, and Data Quality

### Disclosure Control

**Legal Framework**: Controlled under the Census Act 1920 (amended by Census (Confidentiality) Act 1991). No identified individual or household data are released; census forms are sealed for 100 years (until 2092).

**Suppression Thresholds**:
- **SAS**: Not released if <50 residents and <16 households
- **LBS**: Not released if <1,000 residents and <320 households
- **Special Enumeration Districts (SEDs)** (e.g., large prisons, army barracks): Relaxed thresholds; basic counts provided even if above 100 persons

**Cell Modification**: All SAS/LBS cells at ward and ED levels are modified by adding ±1, 0, or +1 in quasi-random patterns (exception: basic counts in Tables 1, 27, 71 where modification would reduce utility).

### Edit and Imputation

**100% Items**: Answers checked for consistency; missing or inconsistent data imputed using the most recently processed record of similar characteristics. Results: Tables generally lack "not stated" categories.

**10% Items**: Edited clerically; tables include "not stated" categories due to complexity of imputation.

### Data Quality Considerations for AI

1. **Imputation Uncertainty**: Wholly absent households and "no-contact" households (~0.5–0.75% of total) are imputed and grouped together in output; true imputation rates are not exposed at ED level.
2. **Modification Noise**: Cell counts at ward/ED level include deliberate quasi-random ±1 modifications, reducing precision for micro-level analysis.
3. **Aggregation**: Some variables are heavily grouped before release (e.g., occupation, workplace address) to prevent disclosure.
4. **10% Sample Design Effects**: The 10% sample introduces design factors not available in output; standard errors cannot be calculated without access to sample documentation.

## 7. Data Access and Machine-Readable Format

### Available Resources from UK Data Service

1. **Census 1991 bulk data** (7z archive, ~800 MB):
   - Compressed archive of all SAS and LBS tables
   - Includes EW and Scotland tables separately
   - Northern Ireland data separate

2. **Metadata Files** (CSV):
   - **Table Code and Names**: Lookup for table identifiers
   - **Small Area Statistics variable metadata**: Cell codes and definitions
   - **Local Base Statistics variable metadata**: Similar for LBS
   - **Geography metadata**: ED/OA codes and corresponding postcodes/wards (separate for EW and Scotland, and Northern Ireland)

3. **Census Questionnaires** (PDF): Scanned forms for reference

### Data Format Implications

The 1991 Census data in the UK Data Service archive is **not raw microdata**. Instead, it consists of:

- **Pre-aggregated tables**: Cross-tabulations at fixed geographic units (ED, ward, district, county, national)
- **CSV lookup files**: Metadata linking table codes to geographic codes and variable definitions
- **No record-level data at small areas**: Unlike modern census releases (e.g., 2021), the 1991 data does not include person/household records; aggregation to ED level is the minimum

**Implication for AI**: Systems must reconstruct analysis from aggregate counts, not individual records. Cross-tabulations are fixed; arbitrary combinations of variables are not possible at ED level without accessing SARs (Samples of Anonymised Records, which are restricted and require secure access).

## 8. Key Constraints and Limitations for AI Systems

1. **Aggregation Lock-In**: Variables are cross-tabulated in fixed combinations. An AI cannot freely combine variables at ED level; it is limited to published table combinations.
2. **Confidentiality Merging**: Some "ED-level" statistics are actually merged areas, obscuring true ED boundaries.
3. **10% Sample Uncertainty**: 10% item tables have unknown sampling error; confidence intervals cannot be calculated without access to design factors.
4. **Historical Comparability**: Variable definitions differ from 1981 and 2001 censuses (e.g., occupational classification, ethnic group categories), requiring careful recoding for time-series analysis.
5. **Geographic Boundary Instability**: ED boundaries changed between 1981 and 1991; conversion requires postcode-level lookup tables to map households across censuses.
6. **Imputation Opacity**: Imputation methods for absent/non-contacted households are documented qualitatively but not exposed at the record level.

## 9. Typical AI Use Cases and Data Pathways

### Use Case 1: Local Area Profiles
- **Query**: Get population, age structure, housing tenure for a specific ward
- **Data Path**: LBS Table 1 (population), Table 2 (age by sex), Table 20 (tenure) at ward level
- **Output**: Pre-aggregated tables; no record-level data

### Use Case 2: Ethnic Segregation Analysis
- **Query**: Ethnic group distribution across EDs in a city
- **Data Path**: SAS Table on ethnic group by ED
- **Challenge**: EDs below 50 residents are merged; analyst must account for merged ED geometry

### Use Case 3: Occupational Geography
- **Query**: Distribution of managers by workplace area
- **Data Path**: SAS/LBS Table on occupation (SOC code) by area
- **Constraint**: Only 10% sample; design effects unknown; 10% sampling variability not documented

### Use Case 4: Historical Comparison (1981–1991)
- **Query**: Population change, housing stock change by area
- **Challenge**: ED boundaries changed; postcode-to-ED mapping required; occupational classification revised
- **Data Path**: Requires postcode-level conversion tables to align 1991 EDs to 1981 EDs

## 10. Recommended AI System Architecture

For robust analysis of 1991 Census data, an AI system should:

1. **Maintain Metadata Dictionaries**:
   - Table code ↔ variable name/definition
   - Geographic code ↔ ED/OA/ward/district geometry (and note merged areas)
   - Variable code ↔ category label/numeric range

2. **Flag Confidentiality Constraints**:
   - Mark suppressed or merged geographic units
   - Document cell modification (±1 noise) in output
   - Estimate sampling error for 10% items (if design factors available)

3. **Support Cross-Temporal Analysis**:
   - Provide conversion functions between 1981, 1991, and 2001 ED/ward boundaries
   - Document variable definition changes (e.g., ethnic group, occupational classification)

4. **Implement Query Validation**:
   - Reject requests for variable combinations not published (e.g., "occupation by ethnic group at ED level" if not in SAS tables)
   - Return aggregated data with appropriate precision disclaimers

5. **Provide Documentation**:
   - Every query result should include metadata: processing level (100% or 10%), population base, confidentiality modifications, and geographic merging notes

---

## Key References

- OPCS/GRO(S). (1992). *1991 Census of Population: Definitions for Great Britain*. HMSO.
- UK Data Service. (2017). *Guide to the 1991 Samples of Anonymised Records*. 
- Manchester Institute for Social and Spatial Change. (2005). *Geographic Conversion and 1991–2001 Census Data Linkage*. Working Paper.
- Wilson, T. (1998). *Look-up Tables to Link 1991 Population Statistics to 1998 Local Authority Areas*. University of Leeds.
