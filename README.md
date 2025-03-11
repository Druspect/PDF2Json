# PDF to JSON Converter

This Python script extracts text and structure from PDF files and converts them into a structured JSON format. It is designed to handle various PDF structures, filter out noise, and provide a clean, hierarchical JSON output suitable for further processing or analysis.

## Features

- Extracts metadata such as title, author, and creation date.
- Processes nested outlines to capture the document's hierarchical structure.
- Filters out common noise like page numbers, headers, and footers.
- Detects images and includes placeholders in the JSON output.
- Standardizes metadata fields for consistency.

- ## Installation

To get started, follow these steps:

1. **Clone the repository**:
     git clone https://github.com/yourusername/pdf-to-json-converter.git

3. **Navigate to the project directory**:
     cd pdf-to-json-converter

4. **Install the required Python packages**:
     pip install -r requirements.txt

## Usage

Run the script from the command line using the following syntax:
- python pdf_to_json.py <input_pdf_path> <output_json_path>
- `<input_pdf_path>`: Path to the input PDF file.
- `<output_json_path>`: Path to the output JSON file where the result will be saved.
  ### Example

  python pdf_to_json.py sample.pdf output.json

  ## Output Format

The output JSON file is organized into two main sections:

- **`metadata`**: Contains document-level information such as title, author, and creation date.
- **`chapters`**: An array of chapter objects (or `content` if no outlines are present), each including:
  - `title`: The chapter title.
  - `level`: The nesting level (0 for top-level chapters).
  - `start_page`: The starting page number.
  - `pages`: An array of text content extracted from each page.
  - `images`: An array of image placeholders (e.g., `"[Image]"`).
 
  - ### Sample JSON Snippet
{
    "metadata": {
        "Title": "Sample Document",
        "Author": "John Doe",
        "CreationDate": "2023-01-01T12:00:00Z"
    },
    "chapters": [
        {
            "title": "Introduction",
            "level": 0,
            "start_page": 1,
            "pages": ["This is the introduction..."],
            "images": ["[Image]"]
        },
        {
            "title": "Chapter 1",
            "level": 0,
            "start_page": 2,
            "pages": ["Chapter 1 content..."],
            "images": []
        }
    ]
}


#### Block 8: Error Handling
## Error Handling

The script includes robust error handling for scenarios such as:

- Missing or invalid PDF files.
- Corrupt PDF documents.
- Extraction failures, with a fallback to flat text extraction if structured parsing fails.

Errors are logged using Python's `logging` module to assist with debugging.

## Contributing

We welcome contributions! To contribute, please follow these steps:

1. **Fork the repository**.
2. **Create a new branch**:
   git checkout -b feature-branch
3. **Make your changes and commit them**:
    git commit -m 'Add new feature'   
4. **Push to the branch**:
  git push origin feature-branch
5. **Open a pull request** on GitHub.

   
 ## Acknowledgments

- [PyPDF2](https://github.com/py-pdf/PyPDF2): For PDF parsing and extraction capabilities.
- [pdfplumber](https://github.com/jsvine/pdfplumber): For advanced PDF layout analysis (optional dependency).
