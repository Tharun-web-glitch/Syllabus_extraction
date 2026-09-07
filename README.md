# 📚 Universal Academic Syllabus Extractor

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A high-performance, hybrid Python pipeline to convert unstructured university syllabus handbooks (PDF) into structured, relational datasets (`.xlsx` and JSON). 

Designed to operate **100% offline and free by default** using deterministic regular expressions and dynamic compound-term shielding, with an optional LLM fallback for ambiguous text and unfamiliar university layouts.

---

## 🚀 Key Features

* **Instantaneous Processing**: Parses 90+ page university handbooks in **under 2 seconds** with zero API costs.
* **Deterministic Two-Pass Architecture**:
  * **Pass 1**: Scans curriculum overview tables to map Course Codes to Semesters accurately.
  * **Pass 2**: Slices continuous, flattened text into courses, units, and contact hours.
* **Dynamic Compound-Term Protection**: Automatically shields multi-word theorems and methods (e.g., *Cayley-Hamilton*, *Runge-Kutta*, *Navier-Stokes*, *p-n junction*, *if-else*) from delimiter fragmentation.
* **Category Normalization**: Resolves dangling language subheadings (*Writing:*, *Grammar:*, *Vocabulary:*) by binding them directly into downstream topic rows.
* **Multi-File Processing**: Drag-and-drop multiple syllabus PDFs simultaneously and export a single, tagged Excel workbook (`SOURCE FILE` column included).
* **Configurable LLM Fallback**: Optional micro-calls using **Anthropic Claude**, **OpenAI**, or **local Ollama (`qwen2.5:3b`)** for ambiguous phrasing or non-standard layouts.

---

## 📊 Benchmark Validation

| Handbook | Pages | Courses Found | Units Found | Topics Extracted | Execution Time |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B.E. Computer Science (CSE)** | 91 | 32 / 32 (100%) | 161 / 161 (100%) | 869 rows | ~1.8s |
| **B.Tech. AI & Data Science (AI-DS)** | 256 | 110 / 110 | 569 units | 3,050 rows | ~3.2s |

---

## 🛠️ Project Structure

```text
├── app.py                 # Streamlit UI & batch pipeline orchestrator
├── pdf_reader.py          # PDF text extraction & Unicode normalizer
├── structural_parser.py   # Two-pass deterministic course & unit boundary parser
├── topic_splitter.py      # Dynamic compound-term shield & topic tokenizer
├── llm_client.py          # Unified LLM client (Anthropic / OpenAI / Ollama)
├── requirements.txt       # Project dependencies
├── DOCUMENTATION.md       # Comprehensive technical & architecture documentation
└── README.md              # Project overview & quickstart guide
