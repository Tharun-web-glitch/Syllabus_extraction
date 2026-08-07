import os
import sys
import json
import io
from typing import List, Optional
import pandas as pd
from pydantic import BaseModel, Field
import pypdf
from google import genai
from google.genai import types

# ==========================================
# 1. PYDANTIC SCHEMAS
# ==========================================

class UnitModule(BaseModel):
    module_no: str = Field(
        description="Unit/Module number or identifier (e.g., 'UNIT I', '1', 'Module A')."
    )
    module_name: str = Field(
        description="Name or title of the unit/module (e.g., 'Matrices and Calculus')."
    )
    topics: List[str] = Field(
        description="List of distinct topics covered within this unit."
    )

class CourseSyllabus(BaseModel):
    semester: Optional[str] = Field(
        default="NOT SPECIFIED",
        description="Semester or Academic Year (e.g., 'SEMESTER I')."
    )
    subject_code: Optional[str] = Field(
        default="NOT SPECIFIED",
        description="Official course/subject code (e.g., '22CSE201')."
    )
    subject_name: str = Field(
        description="Full course or subject name (e.g., 'Data Structures')."
    )
    modules: List[UnitModule] = Field(
        description="List of all units/modules inside this course."
    )

class UniversalSyllabusExtraction(BaseModel):
    syllabi: List[CourseSyllabus] = Field(
        default_factory=list,
        description="All courses found within the PDF segment."
    )


# ==========================================
# 2. CHUNKED EXTRACTION ENGINE
# ==========================================

def split_pdf_bytes(pdf_path: str, chunk_size: int = 10):
    """Splits a large PDF into smaller byte chunks in memory."""
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    
    print(f"Total pages in document: {total_pages}")
    
    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size, total_pages)
        writer = pypdf.PdfWriter()
        
        for p in range(start_page, end_page):
            writer.add_page(reader.pages[p])
            
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        
        yield (start_page + 1, end_page, pdf_bytes)


def extract_chunk(client: genai.Client, pdf_bytes: io.BytesIO, start_p: int, end_p: int) -> UniversalSyllabusExtraction:
    """Processes a chunk of PDF pages using Gemini."""
    print(f"\nProcessing pages {start_p} to {end_p}...")
    
    # Upload byte chunk
    pdf_file = client.files.upload(
        file=pdf_bytes, 
        config=types.UploadFileConfig(mime_type="application/pdf")
    )

    prompt = """
    You are an expert academic document parser.
    Examine the uploaded PDF pages and extract all course syllabi, units/modules, and individual topics present in these pages.

    Rules:
    1. Extract every course/subject present on these pages.
    2. Do NOT split recognized compound terms (e.g., 'Cayley-Hamilton Theorem', 'Gram-Schmidt Process').
    3. Omit administrative content like Course Outcomes, Textbooks, References, and Objectives.
    4. If a page contains no syllabus modules/units, return an empty "syllabi" list.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[pdf_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=UniversalSyllabusExtraction,
                temperature=0.1,
                max_output_tokens=8192
            ),
        )

        if response.parsed is not None:
            return response.parsed

        if response.text:
            return UniversalSyllabusExtraction.model_validate_json(response.text)

        return UniversalSyllabusExtraction(syllabi=[])

    except Exception as e:
        print(f"Warning: Failed to extract pages {start_p}-{end_p}: {e}")
        return UniversalSyllabusExtraction(syllabi=[])
        
    finally:
        try:
            client.files.delete(name=pdf_file.name)
        except Exception:
            pass


def extract_full_syllabus(pdf_path: str, chunk_size: int = 10) -> UniversalSyllabusExtraction:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    client = genai.Client()
    combined_extraction = UniversalSyllabusExtraction(syllabi=[])

    # Process PDF in chunks of 10 pages
    for start_p, end_p, chunk_bytes in split_pdf_bytes(pdf_path, chunk_size=chunk_size):
        chunk_result = extract_chunk(client, chunk_bytes, start_p, end_p)
        if chunk_result and chunk_result.syllabi:
            combined_extraction.syllabi.extend(chunk_result.syllabi)

    return combined_extraction


# ==========================================
# 3. DATAFRAME CONVERSION & EXPORT
# ==========================================

def syllabus_to_dataframe(structured_data: UniversalSyllabusExtraction) -> pd.DataFrame:
    rows = []
    for course in structured_data.syllabi:
        for module in course.modules:
            for topic_str in module.topics:
                rows.append({
                    "SEMESTER": course.semester,
                    "SUBJECT CODE": course.subject_code,
                    "SUBJECT NAME": course.subject_name,
                    "MODULE NO": module.module_no,
                    "MODULE NAME": module.module_name,
                    "TOPIC": topic_str
                })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pdf_file_path = "JNN CSE.pdf"

    if not os.path.exists(pdf_file_path):
        for file in os.listdir("."):
            if file.endswith(".pdf"):
                pdf_file_path = file
                break

    print(f"Target document: {pdf_file_path}")

    try:
        # Process in chunks of 10 pages
        pydantic_output = extract_full_syllabus(pdf_file_path, chunk_size=10)
        df_syllabus = syllabus_to_dataframe(pydantic_output)
        
        excel_output = "Syllabus_Structured_Output.xlsx"
        json_output = "Syllabus_Structured_Output.json"
        
        df_syllabus.to_excel(excel_output, index=False)
        with open(json_output, "w", encoding="utf-8") as f:
            f.write(pydantic_output.model_dump_json(indent=2))

        print("\n Extraction Completed Successfully!")
        print(f"Total topics extracted: {len(df_syllabus)}")
        print(f"Saved Excel file: {excel_output}")

        if not df_syllabus.empty:
            print("\n--- Output Preview ---")
            print(df_syllabus.head(10).to_string())

    except Exception as e:
        print(f"\n Execution Error: {e}", file=sys.stderr)
