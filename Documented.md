## Extraction Approaches & Benchmark Analysis

---

### Approach 1: Heuristic Regex & Rule-Based Parser (Initial Baseline)

* **Stack / Libraries:** Python Native `re`, `pypdf`, `pandas`

#### Use Case(s) Evaluated
* Extract course syllabi, module units, and topics by pattern matching line structures, bullet points, and delimiters.

#### ✅ What Worked Successfully
* **Zero Cost & Fast:** Fast, offline execution with zero API overhead.
* **Predictable Patterns:** Extracted initial semester and subject codes when document layouts remained uniform.

#### ❌ Limitations & Failures
* **Brittle Architecture:** Highly fragile and tightly coupled to a single university's formatting.
* **Hardcoded Logic:** Relied on manual page ranges (`range(18, len(pages))`), batch code regexes (`22[A-Z]...`), and hardcoded subject overrides (`if "Engineering Physics"`).
* **Token Splitting Errors:** Improperly split compound domain terms (e.g., *Cayley-Hamilton Theorem*, *if-else* statements).

> **Key Takeaway:** Regex cannot generalize across multi-column formats, varied table layouts, or heterogeneous department handbooks.

---

### Approach 2: Direct Whole-Document LLM Extraction

* **Model / SDK:** `gemini-2.5-flash` via Google GenAI SDK (`google-genai`)

#### Use Case(s) Evaluated
* Feeding the entire 91-page PDF handbook in a single prompt with a nested Pydantic schema (`UniversalSyllabusExtraction`).

#### ✅ What Worked Successfully
* **Zero Rule-Authoring:** Accurate contextual parsing on initial pages without requiring explicit regex token rules.

#### ❌ Limitations & Failures
* **Output Truncation:** Output truncated abruptly mid-JSON (`Invalid JSON: EOF while parsing a value`).
* **Schema Validation Failure:** `response.parsed` evaluated to `None`, raising `'NoneType' object has no attribute 'syllabi'`.

> **Key Takeaway:** Converting a full 91-page curriculum into a single structured JSON response exceeded the model's output generation limits, terminating the response string prematurely.

---

### Approach 3: In-Memory Chunked LLM Extraction with Pydantic Schema

* **Model / Stack:** `gemini-2.5-flash` (`pydantic` v2, `pypdf` in-memory binary writer via `io.BytesIO`)

#### Use Case(s) Evaluated
* Slicing the PDF into in-memory chunks (10 pages per batch), extracting structured syllabus data per chunk, and concatenating results into a relational `DataFrame`.

#### ✅ What Worked Successfully
* **Efficient Memory Usage:** Solved full-document context bloating by streaming lightweight byte chunks via `io.BytesIO()`.
* **Structured Output:** Successfully extracted nested structures into clean JSON and Excel tables for valid chunks.
* **Resource Cleanup:** Automated cleanup of uploaded files from the Gemini API upon completion.

#### ❌ Limitations & Failures
* **Chunk Token Limits:** Dense chunks (e.g., Pages 29–38, 59–68) with multiple lab courses still hit token truncation (`EOF while parsing`).
* **Context Boundary Loss:** Fixed page slicing split subjects across chunk boundaries, causing dropped topics and missing course codes.
* **Metadata Disconnect:** Body pages lacked top-level semester headers, leaving extracted `SEMESTER` fields as `NOT SPECIFIED` or `NaN`.

> **Key Takeaway:** Static chunking without cross-page state retention or semantic boundary awareness creates data loss at page splits.


## 2. Summary of Models & Techniques Evaluated

| Version / Approach | Core Engine | Primary Use Case | Output Quality | Failure Mode / Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **v1.0 Baseline** | Pure Regex + `pypdf` | Rule-based syllabus parsing | 🔴 Poor / Brittle | Broken terms, non-transferable rules, hardcoded page bounds. |
| **v2.0 Monolithic LLM** | Gemini 2.5 Flash (Full PDF) | End-to-end PDF parsing | ❌ Failed | Output token truncation (`EOF while parsing`), schema validation failure. |
| **v2.1 Chunked LLM (Current)** | Gemini 2.5 Flash + In-Memory Chunks | 10-page chunked JSON extraction | 🟡 Moderate (Best to date) | Missing semesters, boundary splitting, rate limit susceptibility. |

---

## 3. Current Status

The repository is currently hosted with the **In-Memory Chunked Gemini 2.5 Flash parser** (`app.py`).

* Successfully demonstrates end-to-end multimodal extraction from raw PDFs into structured Excel (`.xlsx`) and JSON files.
* Executes completely in-memory using `io.BytesIO()` without relying on hardcoded page ranges or temporary files written to local disk.

---

## 4. Current Blockers & Challenges

* **Free-Tier Rate Limits (`429 RESOURCE_EXHAUSTED`):**
  Rapid sequential chunk execution triggers the Gemini Free Tier threshold (20 RPM), dropping subsequent chunks unless throttled.
* **Chunk Boundary Splitting:**
  Subjects spanning across chunk boundaries are parsed as disconnected entities, often causing missing titles or course codes in the trailing chunk.
* **Semester & Header Disconnect:**
  High-level curriculum overview tables (Semesters I–VIII) are decoupled from the detailed syllabus body, leaving chunk-level extractions without top-level semester metadata.

---

## 5. Next Steps to Proceed Further

- [ ] **Implement Exponential Backoff & Delay Throttling:** Add automated wait-and-retry logic (`time.sleep` / jitter) on `429 RESOURCE_EXHAUSTED` errors to ensure complete pipeline execution under free-tier quotas.
- [ ] **Two-Pass Hybrid Pipeline:**
  - **Pass 1:** Scan initial curriculum structure (Pages 1–18) to construct a lightweight master lookup mapping: `Course Code` $\rightarrow$ `Semester`.
  - **Pass 2:** Extract syllabus modules via chunking and join missing metadata against the Pass 1 master map.
- [ ] **Dynamic Overlap / Subject-Aware Slicing:** Replace rigid 10-page slicing with a sliding window (e.g., 1-page overlap) or outline/bookmark detection to eliminate cross-chunk subject truncation.

```
