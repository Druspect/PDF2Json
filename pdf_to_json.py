import PyPDF2
import json
import argparse
import os
import re
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_text_from_page(page):
    """
    Extract text from a PDF page, filtering out headers, footers, and noise.

    Args:
        page: A PyPDF2 page object.

    Returns:
        str: Filtered text content.
    """
    text = page.extract_text()
    if not text:
        return ""
    # Split text into lines
    lines = text.split('\n')
    # Filter out standalone numbers (e.g., page numbers) and common noise patterns
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are just numbers, dates, or short noise
        if (not re.match(r'^\s*\d+\s*$', stripped) and
                not stripped.isdigit() and
                not re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', stripped) and  # Skip dates
                len(stripped) > 2):  # Skip very short lines
            filtered_lines.append(line)
    return '\n'.join(filtered_lines)

def extract_image_info(page):
    """
    Detect images on a page and return placeholders or captions if available.

    Args:
        page: A PyPDF2 page object.

    Returns:
        list: List of image placeholders or captions.
    """
    images = []
    # Check for XObject resources containing images
    if '/XObject' in page['/Resources']:
        xobjects = page['/Resources']['/XObject'].get_object()
        for obj in xobjects:
            if xobjects[obj]['/Subtype'] == '/Image':
                # Limited caption detection with PyPDF2; use placeholder
                images.append("[Image]")
    return images

def process_outlines(reader, outlines, level = 0):
    """
    Recursively process PDF outlines to capture hierarchical structure.

    Args:
        reader: PyPDF2 PdfReader object.
        outlines: List of outline objects or nested lists.
        level: Current nesting level (default 0 for top-level).

    Returns:
        list: List of chapter dictionaries with title, level, and start_page.
    """
    chapters = []
    for outline in outlines:
        if isinstance(outline, list):
            sub_chapters = process_outlines(reader, outline, level + 1)
            chapters.extend(sub_chapters)
        else:
            try:
                title = outline.title
                start_page = reader.get_destination_page_number(outline)
                chapters.append({
                    'title': title,
                    'level': level,
                    'start_page': start_page
                })
            except AttributeError as e:
                logging.warning(f"Skipping invalid outline entry: {e}")
    return chapters

def standardize_metadata(metadata):
    """
    Standardize and validate metadata fields.

    Args:
        metadata: Dictionary of metadata from the PDF.

    Returns:
        dict: Standardized metadata.
    """
    if not metadata:
        return {'Title': 'Untitled', 'Author': 'Unknown'}

    standardized = {}
    for key, value in metadata.items():
        clean_key = key.lstrip('/')
        if clean_key in ['CreationDate', 'ModDate'] and value:
            # Parse PDF date (e.g., "D:20230115123456") to ISO 8601
            try:
                date_str = value[2:16] if value.startswith('D:') else value
                date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                standardized[clean_key] = date_obj.isoformat() + 'Z'
            except (ValueError, TypeError):
                standardized[clean_key] = value  # Keep original if parsing fails
        else:
            standardized[clean_key] = value
    # Ensure required fields
    if 'Title' not in standardized or not standardized['Title']:
        standardized['Title'] = 'Untitled'
    if 'Author' not in standardized or not standardized['Author']:
        standardized['Author'] = 'Unknown'
    return standardized

def pdf_to_json(pdf_path, json_path):
    """
    Convert a PDF file to a JSON file with enhanced features.

    Args:
        pdf_path (str): Path to the input PDF file.
        json_path (str): Path to the output JSON file.
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # Extract and standardize metadata
            metadata = reader.metadata or {}
            metadata_dict = standardize_metadata(metadata)

            # Process outlines for chapter structure
            outlines = reader.outline
            if outlines:
                chapters = process_outlines(reader, outlines)
                if not chapters:
                    logging.warning("No valid outlines found; treating as flat content")
                    outlines = []
                else:
                    chapters.sort(key=lambda x: x['start_page'])
                    for i, chapter in enumerate(chapters):
                        start_page = chapter['start_page']
                        end_page = chapters[i + 1]['start_page'] - 1 if i < len(chapters) - 1 else len(reader.pages) - 1
                        chapter_text = []
                        chapter_images = []
                        for page_num in range(start_page, end_page + 1):
                            page = reader.pages[page_num]
                            text = extract_text_from_page(page)
                            images = extract_image_info(page)
                            chapter_text.append(text)
                            chapter_images.extend(images)
                        chapter['pages'] = chapter_text
                        chapter['images'] = chapter_images
                    json_data = {
                        'metadata': metadata_dict,
                        'chapters': chapters
                    }

            if not outlines or not chapters:
                # Fallback to flat content extraction
                content = []
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = extract_text_from_page(page)
                    images = extract_image_info(page)
                    content.append({'text': text, 'images': images})
                json_data = {
                    'metadata': metadata_dict,
                    'content': content
                }

            # Write to JSON file with validation
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, indent=4, ensure_ascii=False)
            logging.info(f"Successfully converted {pdf_path} to {json_path}")

    except FileNotFoundError:
        logging.error(f"File not found: {pdf_path}")
    except PyPDF2.errors.PdfReadError:
        logging.error(f"Invalid PDF file: {pdf_path}")
    except Exception as e:
        logging.error(f"Error processing {pdf_path}: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a PDF file to JSON format with enhanced features")
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument("json_path", help="Path to the output JSON file")
    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.pdf_path):
        logging.error(f"{args.pdf_path} does not exist")
    elif not args.pdf_path.lower().endswith('.pdf'):
        logging.error("Input file must be a PDF")
    else:
        pdf_to_json(args.pdf_path, args.json_path)