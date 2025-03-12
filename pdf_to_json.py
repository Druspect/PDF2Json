import PyPDF2
import json
import argparse
import os
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_text(page):
    text = page.extract_text() or ""
    return '\n'.join([line.strip() for line in text.split('\n') if len(line.strip()) > 2 and not re.match(r'^(\d+|\d{1,2}/\d{1,2}/\d{2,4})$', line.strip())])

def extract_images(page):
    return ["[Image]"] if '/XObject' in page['/Resources'] and any(x['/Subtype'] == '/Image' for x in page['/Resources']['/XObject'].get_object().values()) else []

def process_outlines(reader, outlines, level=0):
    chapters = []
    for outline in outlines:
        if isinstance(outline, list):
            chapters.extend(process_outlines(reader, outline, level + 1))
        else:
            try:
                chapters.append({
                    'title': outline.title,
                    'level': level,
                    'start_page': reader.get_destination_page_number(outline)
                })
            except AttributeError:
                continue
    return chapters

def standardize_metadata(metadata):
    if not metadata:
        return {'Title': 'Untitled', 'Author': 'Unknown'}
    standardized = {key.lstrip('/'): metadata[key] for key in metadata}
    for key in ['CreationDate', 'ModDate']:
        if key in standardized and standardized[key].startswith('D:'):
            try:
                standardized[key] = datetime.strptime(standardized[key][2:16], '%Y%m%d%H%M%S').isoformat() + 'Z'
            except ValueError:
                pass
    standardized.setdefault('Title', 'Untitled')
    standardized.setdefault('Author', 'Unknown')
    return standardized

def pdf_to_json(pdf_path, json_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            metadata_dict = standardize_metadata(reader.metadata or {})
            outlines = process_outlines(reader, reader.outline) if reader.outline else []
            
            if outlines:
                for i, chapter in enumerate(outlines):
                    start, end = chapter['start_page'], (outlines[i + 1]['start_page'] - 1 if i < len(outlines) - 1 else len(reader.pages) - 1)
                    chapter.update({'pages': [extract_text(reader.pages[p]) for p in range(start, end + 1)],
                                    'images': sum([extract_images(reader.pages[p]) for p in range(start, end + 1)], [])})
                json_data = {'metadata': metadata_dict, 'chapters': outlines}
            else:
                json_data = {'metadata': metadata_dict, 'content': [{'text': extract_text(p), 'images': extract_images(p)} for p in reader.pages]}

            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, indent=4, ensure_ascii=False)
            logging.info(f"Successfully converted {pdf_path} to {json_path}")
    except (FileNotFoundError, PyPDF2.errors.PdfReadError) as e:
        logging.error(f"Error processing {pdf_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a PDF file to JSON format")
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument("json_path", help="Path to the output JSON file")
    args = parser.parse_args()

    if os.path.exists(args.pdf_path) and args.pdf_path.lower().endswith('.pdf'):
        pdf_to_json(args.pdf_path, args.json_path)
    else:
        logging.error("Invalid file path or type")
