## Current Approach: In-Memory Chunked LLM Extraction (v2.1)

## 🛠️ Current Approach: In-Memory Chunked LLM Extraction

To overcome context window limits and eliminate fragile regex rules, the parser currently uses **Gemini 2.5 Flash** combined with **In-Memory PDF Chunking** and **Pydantic schema validation**.

┌─────────────────┐       ┌────────────────────────┐       ┌───────────────────────┐
│   Syllabus PDF  │ ───►  │  In-Memory Chunking    │ ───►  │  Gemini 2.5 Flash     │
│    (Full Doc)   │       │ (pypdf / 10-pg slices) │       │ (Strict JSON Schema)  │
└─────────────────┘       └────────────────────────┘       └───────────────────────┘
│
┌─────────────────┐       ┌────────────────────────┐                   ▼
│  Excel & JSON   │ ◄───  │ Tabular Flattening     │ ◄───  ┌───────────────────────┐
│     Outputs     │       │   (Pandas DataFrame)   │       │ Pydantic Validation   │
└─────────────────┘       └────────────────────────┘       └───────────────────────┘


---

### How the Pipeline Works

1. **In-Memory Page Slicing (`pypdf`):**
   * Instead of sending an entire 90+ page document at once, the script slices the PDF into **10-page binary chunks** (`io.BytesIO`) directly in RAM without saving temp files to disk.

2. **Multimodal Extraction (Gemini 2.5 Flash):**
   * Each chunk is sent to Gemini with a strict schema enforcement prompt to extract:
     * **Course Code & Title**
     * **Semester / Year**
     * **Unit / Module Names & Numbers**
     * **Granular Topic Lists**
   * Administrative sections (Textbooks, Course Outcomes, Marks) are filtered out automatically.

3. **Schema Enforcement (`Pydantic v2`):**
   * Guarantees the output matches a strict JSON contract (`UniversalSyllabusExtraction`).
   * Falls back to manual JSON string validation (`model_validate_json`) if automatic parsing returns `None`.

4. **Data Flattening & Export (`pandas`):**
   * Concatenates all chunks and unrolls nested hierarchies into flat tabular rows:
     * `Syllabus_Structured_Output.xlsx` (Excel Spreadsheet)
     * `Syllabus_Structured_Output.json` (Structured JSON Hierarchy)
   * Automatically deletes uploaded remote chunk files from the Gemini API server.

---

* **Model / Version:** `gemini-2.5-flash` with Pydantic v2 & `pypdf` in-memory binary writer.
* **How It Works:** Slices the full PDF into 10-page chunks in RAM (`io.BytesIO()`), sends each chunk to Gemini to extract structured topics, and merges everything into an Excel sheet.

### What Worked Well ✅
* **No Huge Files:** Slicing pages in memory prevented token overflow from sending the entire PDF at once.
* **Structured Output:** Automatically extracted courses, modules, and topics into clean JSON and Excel formats.
* **Automatic Cleanup:** Successfully deleted temporary files from the Gemini API after each request.

### What Didn't Work / Limitations ⚠️
* **Token Limit Truncation:** Large or dense page chunks (like lab experiment lists) still exceeded token output limits, causing `EOF while parsing` JSON errors.
* **Split Headers:** Slicing by fixed 10-page blocks cut some subjects in half across chunks, losing course codes and titles.
* **Missing Semesters:** Detailed syllabus pages did not repeat top-level semester names, leading to `NOT SPECIFIED` values in the output.
* **Rate Limits:** Rapid sequential calls without delays occasionally hit Gemini's free-tier rate limits (`429 RESOURCE_EXHAUSTED`).

### Key Takeaway 💡
Chunking pages in memory keeps prompts small, but it needs smaller chunks (or delay throttling) and a pre-mapping step to capture missing semester information reliably.
