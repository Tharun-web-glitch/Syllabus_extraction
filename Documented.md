# Universal Academic Syllabus Extractor & Semantic Topic Mapper

## Engineering & Architecture Documentation

### Project Overview
The **Universal Academic Syllabus Extractor** is a hybrid, production-grade document intelligence pipeline designed to extract deeply nested academic curriculum structures (Semesters, Course Codes, Course Titles, Module/Unit numbers, Unit Names, and granular Topics) from unstructured, multi-column university PDF handbooks into relational datasets (Excel `.xlsx` and JSON).

---

## 1. Architecture Evolution & Benchmarked Approaches

| Version / Approach | Core Engine | Primary Strategy | Throughput / Speed | Output Coverage | Failure Modes & Trade-offs |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **v1.0 Baseline** | Pure Regex + `pypdf` | Line-by-line regex scanning with hardcoded boundaries | < 1 sec | Poor (~30%) | Broken terms, non-transferable rules, line wraps broke multi-line titles. |
| **v2.0 Monolithic LLM** | `gemini-2.5-flash` | Full 91-page PDF context passed to Gemini via Pydantic schema | ~45 sec | Failed (0%) | Token generation exhaustion (`EOF while parsing`), truncated JSON. |
| **v2.1 Chunked LLM** | `gemini-2.5-flash` | 10-page fixed in-memory byte chunks via `io.BytesIO()` | ~2.5 min | Moderate (~65%) | Courses split across arbitrary chunk boundaries; missing semester mappings. |
| **v2.2 Multi-Key Cloud** | `gemini-2.5-flash` | Pass 1 overview pre-mapper + dynamic 2-course batches with key rotation | ~1.5 min | High (Intermittent) | Hard `403 PERMISSION_DENIED` key revocation; free-tier rate limits. |
| **v3.0 Heavy Local LLM** | Ollama (`qwen2.5:7b`) | 100% offline schema extraction on local hardware | > 1.5 hrs | High (~85%) | CPU bottleneck on consumer laptops; lost progress on execution interruption. |
| **v3.1 Resumable Local** | Ollama (`qwen2.5:3b`) | Checkpoint manager (`syllabus_checkpoint.json`) + delimiter splitting | ~10–12 min | High (~88%) | Delimiters fragmented scientific terms (*Cayley* / *Hamilton*); stray labs passed through. |
| **v4.0 Hybrid Baseline** | Loose Regex + Guard List | Fast Streamlit parser with hardcoded word guard list | < 2 sec | Moderate (781 rows) | Corrupted course codes (`STATISTICS`, `COURSE`); dropped Unit 1s. |
| **v4.1 Sanitized Regex** | Strict Codes + Overview Scan | Alphanumeric code validation (`22[A-Z]{2,4}\d{3}`) | < 2 sec | High (776 rows) | Single-line regex failed to capture multi-line unit headers across 12 courses. |
| **v4.2 Lookahead Parser** | Sliding Window Regex | 3-line sliding window lookahead + Unicode dash normalizer | < 2 sec | Very High (857 rows) | Dropped alphanumeric titles (`5G`), special symbols (`C++`), and long titles. |
| **v4.3 Production Hybrid** *(Current)* | Flattened Regex + Dynamic Shield + Two-Pass Overview | Two-pass flattened string scanning + Title-Case regex compound protection | **1–3 sec** | **State-of-the-Art (869 / 3,050 rows)** | Non-credit Mandatory Course tables placed on trailing pages require deep overview scanning. |

---

## 2. Core System Architecture

========================================================================================
                                PIPELINE ARCHITECTURE
========================================================================================

 [ Upload PDF Handbooks ]
            │
            ▼
 ┌────────────────────────────────────────────────────────────────────────────────────┐
 │ STAGE 1: INGESTION & TEXT NORMALIZATION (pdf_reader.py)                             │
 │   - Extract per-page text stream via PyPDF                                         │
 │   - Strip layout noise & page-number footers ("Page X of Y")                       │
 │   - Normalize Unicode characters (em-dashes '—', en-dashes '–', smart quotes '“' '”')│
 └────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │
                                      ▼
 ┌────────────────────────────────────────────────────────────────────────────────────┐
 │ STAGE 2: TWO-PASS STRUCTURAL PARSER (structural_parser.py)                          │
 │                                                                                    │
 │   [PASS 1: Overview Semester Pre-Mapping]                                          │
 │   - Scans curriculum tables (Pages 1–18)                                           │
 │   - Builds authoritative lookup dictionary: { Course Code -> Semester }            │
 │   - Resolves generic pooled electives (e.g., "NCC Level-I" -> "SEMESTER II")       │
 │                                                                                    │
 │   [PASS 2: Continuous Text Boundary Slicing]                                       │
 │   - Flattens syllabus body into continuous text (repairs multi-line wrapped breaks)│
 │   - Identifies Course Code + Title via flexible credit lookahead (L-T-P-J-C rows)  │
 │   - Carves Unit blocks (UNIT / MODULE / CHAPTER / PART) & contact hours            │
 │   - Truncates at end markers (Textbooks, References, Course Outcomes)              │
 └────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │
                         Confidence Evaluation Check
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
       [ Confidence >= 0.4 ]                         [ Confidence < 0.4 ]
               │                                             │
               │ (Standard Layout)                           │ (Unrecognized Layout)
               ▼                                             ▼
 ┌────────────────────────────────────────┐     ┌────────────────────────────────────┐
 │ STAGE 3: SEMANTIC TOPIC TOKENIZER      │     │ WHOLE-DOCUMENT FALLBACK            │
 │ (topic_splitter.py)                    │     │ (llm_client.py)                    │
 │                                        │     │ - Slices document into chunks      │
 │ 1. Dynamic Compound Shield:            │     │ - Extracts JSON schema via Claude, │
 │    Masks Title-Cased pairs             │     │   OpenAI, or local Ollama          │
 │    ("Cayley-Hamilton" -> "\uE000")     │     └─────────────────┬──────────────────┘
 │    & technical tokens (p-n, if-else)   │                       │
 │                                        │                       │
 │ 2. Delimiter Split:                    │                       │
 │    Splits on ' - ', ' – ', ';'         │                       │
 │                                        │                       │
 │ 3. Heuristic Ambiguity Check:          │                       │
 │    - If unresolved: optional Micro-LLM │                       │
 │    - Else: Restore shielded characters │                       │
 │                                        │                       │
 │ 4. Category Healing:                   │                       │
 │    Merges "Writing:", "Grammar:" tags  │                       │
 └──────────────────┬─────────────────────┘                       │
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
 ┌────────────────────────────────────────────────────────────────────────────────────┐
 │ DATASET AGGREGATION & EXPORT (app.py)                                              │
 │   - Appends all courses across all uploaded PDFs                                   │
 │   - Generates unified relational schema:                                           │
 │     [ SEMESTER | SUBJECT CODE | SUBJECT NAME | MODULE NO | MODULE NAME | TOPIC |   │
 │       SOURCE FILE ]                                                                │
 │   - Interactive Dataframe Preview & Download as Excel (.xlsx)                      │
 └────────────────────────────────────────────────────────────────────────────────────┘
========================================================================================

The pipeline uses a **three-tier deterministic-first design** with zero mandatory API requirements:
### Module Breakdown
1. **`pdf_reader.py`**: Extracts text page-by-page, strips page footers (`Page X of Y`), and normalizes Unicode quotation marks, em-dashes (`—`), and en-dashes (`–`).
2. **`structural_parser.py`**:
   * **Pass 1 (Overview Pre-Mapper)**: Scans curriculum overview tables to map each course code and generic pooled elective (`NCC Level-I/II`) to its authoritative semester.
   * **Pass 2 (Boundary Segmentation)**: Flattens pages into continuous text strings, anchors courses using alphanumeric code patterns with flexible credit lookahead (`L T P J C`, `Credits: X`, or zero-credit lines `3 0 0 0 0`), and slices units using a multi-line lookahead regex.
3. **`topic_splitter.py`**:
   * **Dynamic Guard List**: Detects title-cased hyphenated pairs (`[A-Z][a-z]+-[A-Z][a-z]+`) and technical tokens (`p-n`, `if-else`, `in-situ`), replacing hyphens with a private Unicode placeholder (`\uE000`) prior to splitting.
   * **Category Merging**: Binds dangling category labels (`Writing`, `Grammar`, `Vocabulary`, `Speaking`) directly to the subsequent topic.
4. **`llm_client.py`**: Provider-agnostic client supporting Anthropic Claude, OpenAI, and local Ollama. Used strictly for ambiguous topic chunks or as a whole-document fallback for non-standard formats.

---

## 3. Verified Benchmark Results

### Benchmark 1: `JNN CSE.pdf` (91 Pages)
* **Status**: **100% Structural Coverage**
* **Theory Courses Extracted**: 32 / 32
* **Units Extracted**: 161 / 161 (All courses contain 5 units; Engineering Graphics contains 6 units)
* **Total Topic Rows**: 869 rows
* **Compound Term Integrity**: Verified intact (e.g., `Cayley - Hamilton theorem` preserved as a single row)
* **Execution Time**: 1.8 seconds on standard CPU

### Benchmark 2: `JNN AI DS.pdf` (256/310 Pages)
* **Status**: **96.4% Course Completeness**
* **Theory Courses Extracted**: 110 courses across Semesters I through VIII
* **Units Extracted**: 569 unit blocks
* **Total Topic Rows**: 3,050 rows
* **Execution Time**: 3.2 seconds on standard CPU

---

## 4. Current Limitations & Edge Cases Under Active Work
1. **Mandatory Elective Overview Scanning**: Courses placed in auxiliary non-credit tables at the end of the overview section (`22MCT001`–`22MCT011`) default to `SEMESTER: NOT SPECIFIED` if the overview boundary cut-off is placed before page 18.
2. **Unit Title Character Length Constraints**: Unusually long unit titles (> 90 characters, e.g., German Level I Unit 1 at 108 characters) require relaxed regex length bounds (`{1,160}`).
3. **Industry Annex Agendas**: Industry certification course outlines (e.g., IBM SPSS Modeler / Watson) using non-standard `Duration: (X hrs)` formatting can register as false-positive units under preceding course blocks.

---

## 5. Roadmap
- [x] High-speed deterministic structural parser with multi-line lookahead.
- [x] Dynamic compound scientific term protection.
- [x] Streamlit multi-file upload with consolidated Excel export.
- [ ] Expand overview scan window to cover late-stage non-credit tables (Pages 15–20).
- [ ] Implement Table of Contents (TOC) extraction to support textbook page retrieval.
- [ ] Add embedding-based similarity search (`sentence-transformers`) for automated topic-to-page syllabus mapping.

