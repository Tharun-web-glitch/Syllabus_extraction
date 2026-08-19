## Current Approach: In-Memory Chunked LLM Extraction (v2.1)

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
