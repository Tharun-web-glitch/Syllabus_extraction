import re
import pypdf
import pandas as pd

def build_semester_mapping(reader):
    subject_sem_map = {
        "22LET201": "SEMESTER II", "22LET202": "SEMESTER II",
        "22LET203": "SEMESTER II", "22LET204": "SEMESTER II",
        "22NCC201": "SEMESTER II", "22NCC202": "SEMESTER II",
        "22NCC203": "SEMESTER II",
    }
    current_sem = "SEMESTER I"
    sem_regex = re.compile(r'^\s*SEMESTER\s+([I|V|X]+|\d+)\b', re.IGNORECASE)
    code_regex = re.compile(r'\b(22[A-Z]{2,3}\d{3})\b')

    for page_idx in range(4, 12):
        text = reader.pages[page_idx].extract_text()
        if not text:
            continue
        for line in text.split('\n'):
            sem_match = sem_regex.match(line.strip())
            if sem_match:
                current_sem = f"SEMESTER {sem_match.group(1)}"
            for code in code_regex.findall(line):
                if code not in subject_sem_map:
                    subject_sem_map[code] = current_sem

    return subject_sem_map

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_syllabus(pdf_path):
    rows = []
    ignored_topic_labels = {
        "WRITING", "GRAMMAR", "VOCABULARY", "SPEAKING", "READING", 
        "LIST OF EXPERIMENTS", "EXPERIMENTS", "SYLLABUS", "VERSION",
        "COURSE OBJECTIVES:", "COURSE OUTCOME:"
    }

    reader = pypdf.PdfReader(pdf_path)
    sem_map = build_semester_mapping(reader)
    
    for page_num in range(18, len(reader.pages)):
        text = reader.pages[page_num].extract_text()
        if not text:
            continue

        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # 1. Identify Course Code
        course_code = None
        for line in lines[:10]:
            match = re.search(r'\b(22[A-Z]{2,3}\d{3})\b', line)
            if match:
                course_code = match.group(1)
                break
        
        if not course_code:
            continue

        semester = sem_map.get(course_code, "SEMESTER I")

        # 2. Complete Multiline Subject Title Extraction
        course_title = ""
        for i, line in enumerate(lines[:10]):
            if course_code in line or "Course Title" in line or "COURSE TITLE" in line:
                # Accumulate current line and up to 2 subsequent lines
                combined_title_block = " ".join(lines[i:min(i+3, len(lines))])
                
                # Strip metadata, code, credit numbers, version tags
                cleaned = combined_title_block.replace(course_code, '')
                cleaned = re.sub(r'(?i)\b(Course\s*Title|Course\s*Code|L\s*T\s*P\s*J\s*C|Syllabus|version|v\.\s*\d+\.\d+|NIL)\b', '', cleaned)
                cleaned = re.sub(r'[\d\s]{3,}', ' ', cleaned)
                cleaned = clean_text(re.sub(r'(?i)(COURSE OBJECTIVES|Unit|UNIT).*', '', cleaned))
                
                if len(cleaned) > 2:
                    course_title = cleaned
                    break

        # 3. Complete Multiline Module Name & Topic Extraction
        current_unit_no = ""
        current_unit_name = ""

        i = 0
        while i < len(lines):
            line = lines[i]
            unit_match = re.match(r'^(UNIT|Unit)[-\s]*(\d+|[I|V|X]+)\s*(.*)$', line)
            if unit_match:
                current_unit_no = unit_match.group(2)
                raw_unit_name = unit_match.group(3)
                
                # Check if unit name spills over onto the next line
                if i + 1 < len(lines) and not re.search(r'\d+(\+\d+)?\s*HOURS', raw_unit_name, flags=re.IGNORECASE):
                    next_l = lines[i+1]
                    if not re.search(r'(Writing|Grammar|Vocabulary|COURSE|UNIT|\d+\s*HOURS)', next_l, flags=re.IGNORECASE):
                        raw_unit_name += " " + next_l
                        i += 1
                        
                current_unit_name = clean_text(re.sub(r'\d+(\+\d+)?\s*HOURS.*', '', raw_unit_name, flags=re.IGNORECASE))
                i += 1
                continue

            if current_unit_no and not re.match(r'^(COURSE OBJECTIVES|COURSE OUTCOME|TEXT BOOK|REFERENCE|TOTAL)', line, re.IGNORECASE):
                parts = re.split(r'[–—;]', line)
                for part in parts:
                    cleaned_topic = clean_text(part)
                    
                    if (len(cleaned_topic) > 3 and 
                        cleaned_topic.upper() not in ignored_topic_labels and 
                        not re.match(r'^\d+(\+\d+)?\s*HOURS$', cleaned_topic, flags=re.IGNORECASE)):
                        
                        rows.append({
                            "SEMESTER": semester,
                            "SUBJECT CODE": course_code,
                            "SUBJECT NAME": course_title,
                            "MODULE_No": current_unit_no,
                            "MODULE NAME": current_unit_name,
                            "TOPIC": cleaned_topic
                        })
            i += 1

    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = extract_syllabus("JNN CSE.pdf")
    df.to_excel("Syllabus_Structured_Output_Perfect.xlsx", index=False)
    print("Extraction complete! Output saved to Syllabus_Structured_Output_Perfect.xlsx")