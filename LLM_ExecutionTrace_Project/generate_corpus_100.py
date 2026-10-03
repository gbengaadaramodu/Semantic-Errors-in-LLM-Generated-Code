import json
import openpyxl
from pathlib import Path

# 1. Read the exact 100 trace_ids from the generated Excel file
excel_path = Path('annotation/Annotator_Task_100.xlsx')
wb = openpyxl.load_workbook(excel_path, read_only=True)
ws = wb.active

selected_trace_ids = set()
# Iterate over rows, skipping the header
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0:
        continue
    trace_id = row[0]
    if trace_id:
        selected_trace_ids.add(trace_id)

print(f"Extracted {len(selected_trace_ids)} unique trace_ids from the Excel sheet.")

# 2. Load the full JSON corpus
corpus_path = Path('annotation/Validation_Corpus.json')
with open(corpus_path, 'r', encoding='utf-8') as f:
    full_corpus = json.load(f)

print(f"Loaded {len(full_corpus)} records from the full corpus.")

# 3. Filter the JSON corpus to only include the selected trace_ids
filtered_corpus = [record for record in full_corpus if record.get('trace_id') in selected_trace_ids]

print(f"Filtered down to {len(filtered_corpus)} records.")

# 4. Save to a new JSON file
output_path = Path('annotation/Validation_Corpus_100.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(filtered_corpus, f, indent=4)

print(f"Successfully saved the 100-case JSON corpus to {output_path}")
