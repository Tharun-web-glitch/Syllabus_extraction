
Universal Academic Syllabus Extractor
  A Python tool that extracts, structures, and exports course syllabi from PDF documents into Excel (.xlsx) and JSON formats using the Gemini API and Pydantic.

📌 Features
AI-Powered Parsing: Uses Gemini 2.5 Flash to automatically extract course codes, titles, modules, and topics.
In-Memory Chunking: Splits large PDFs into smaller page chunks using pypdf to prevent memory and token output limits.
Structured Output: Exports data into clean Excel spreadsheets (.xlsx) and hierarchical JSON files (.json).

How It Works
Chunking: The script splits the PDF into 10-page chunks in memory.
LLM Processing: Each chunk is sent to the Gemini API with a strict Pydantic schema to extract courses and topics.
Data Flattening: Extracted nested data is flattened into a Pandas DataFrame and saved as an Excel spreadsheet.

Limitations:
Rate Limits (429 Error): Rapid chunk requests can exceed Gemini's free tier quota (20 requests/min), causing API failures and missing output rows.  
Response Truncation (EOF Error): Heavy text chunks can cause Gemini to hit its 8,192 token output limit, cutting off the JSON mid-sentence and causing parsing errors.
Split Page Context: Fixed page chunking (e.g., 1–10, 11–20) can cut a course in half, causing the AI to miss course codes or titles.
Missing Semester Data: Detailed syllabus pages rarely repeat top-level headers like SEMESTER I, causing the output to default to "NOT SPECIFIED".
Internet Dependency: Requires a continuous internet connection and an active GEMINI_API_KEY to run.
