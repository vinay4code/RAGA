import os
import re
from typing import List, Dict, Any, Tuple
import pymupdf  # PyMuPDF
from bs4 import BeautifulSoup

VERSION_REGEX = re.compile(r'(?:version|v|rel(?:ease)?)\s*[:#]?\s*(\d+(?:\.\d+)*(?:-[a-zA-Z0-9.]+)?)|(?:\b[vV](\d+\.\d+(?:\.\d+)?)\b)', re.IGNORECASE)
DATE_REGEX = re.compile(r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE)

def detect_version_and_date(text: str, filename: str = "") -> Tuple[str, str]:
    version = None
    last_updated = None

    # Check filename first for version
    fn_v_match = VERSION_REGEX.search(filename)
    if fn_v_match:
        version = fn_v_match.group(1) or fn_v_match.group(2)
        if version and not version.lower().startswith('v'):
            version = f"v{version}"

    # Search first 1500 chars of text
    header_text = text[:1500]
    if not version:
        v_match = VERSION_REGEX.search(header_text)
        if v_match:
            version = v_match.group(1) or v_match.group(2)
            if version and not version.lower().startswith('v'):
                version = f"v{version}"

    d_match = DATE_REGEX.search(header_text)
    if d_match:
        last_updated = d_match.group(0)

    return version or "1.0", last_updated or "2024-01-01"

def sanitize_text(text: str) -> str:
    """Clean whitespace and remove control chars while preserving newlines and markdown."""
    text = re.sub(r'[\r\f\v]', '\n', text)
    # Remove repeated spaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract sections and pages from PDF with PyMuPDF."""
    doc = pymupdf.open(file_path)
    filename = os.path.basename(file_path)
    full_sample = ""
    for p_idx in range(min(2, len(doc))):
        full_sample += doc[p_idx].get_text() + "\n"
    
    global_version, global_date = detect_version_and_date(full_sample, filename)

    sections = []
    current_section = "Overview"

    for page_num in range(len(doc)):
        page = doc[page_num]
        text_page = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
        page_text_blocks = []

        for block in text_page:
            if block[6] == 0:  # text block
                b_text = block[4].strip()
                if not b_text:
                    continue

                lines = b_text.splitlines()
                first_line = lines[0].strip()

                # Heuristic for section heading: short first line, title case or all caps, or ends with colon
                if len(first_line) < 80 and (
                    first_line.isupper() or 
                    re.match(r'^(?:[0-9]+(?:\.[0-9]+)*\s+[A-Z]|Chapter|Section|[A-Z][a-zA-Z0-9\s,&/\-]{2,40}$)', first_line)
                ) and len(lines) == 1:
                    current_section = first_line.rstrip(':')
                    continue

                page_text_blocks.append(b_text)

        joined_page_text = "\n\n".join(page_text_blocks)
        if joined_page_text.strip():
            sections.append({
                "content": sanitize_text(joined_page_text),
                "section": current_section,
                "page_number": page_num + 1,
                "version": global_version,
                "last_updated": global_date
            })

    doc.close()
    return sections

def parse_html(file_path: str) -> List[Dict[str, Any]]:
    """Parse HTML documents, sanitizing scripts and extracting sections from headers."""
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # Security sanitize: strip scripts, styles, iframes, and objects
    for tag in soup(["script", "style", "noscript", "iframe", "object", "embed"]):
        tag.decompose()

    raw_text = soup.get_text()
    global_version, global_date = detect_version_and_date(raw_text, filename)

    sections = []
    current_heading = "General"
    current_content = []

    # Iterate through top-level block elements
    body = soup.body or soup
    elements = body.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'table', 'blockquote', 'pre'])

    for el in elements:
        tag_name = el.name.lower()
        if tag_name in ['h1', 'h2', 'h3', 'h4']:
            if current_content:
                text_block = "\n\n".join(current_content)
                if text_block.strip():
                    sections.append({
                        "content": sanitize_text(text_block),
                        "section": current_heading,
                        "page_number": 1,
                        "version": global_version,
                        "last_updated": global_date
                    })
                current_content = []
            current_heading = el.get_text().strip()
        else:
            txt = el.get_text().strip()
            if txt:
                current_content.append(txt)

    if current_content:
        text_block = "\n\n".join(current_content)
        if text_block.strip():
            sections.append({
                "content": sanitize_text(text_block),
                "section": current_heading,
                "page_number": 1,
                "version": global_version,
                "last_updated": global_date
            })

    if not sections and raw_text.strip():
        sections.append({
            "content": sanitize_text(raw_text),
            "section": "Main",
            "page_number": 1,
            "version": global_version,
            "last_updated": global_date
        })

    return sections

def parse_markdown(file_path: str) -> List[Dict[str, Any]]:
    """Parse Markdown with heading hierarchy and frontmatter detection."""
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    full_text = "".join(lines)
    global_version, global_date = detect_version_and_date(full_text, filename)

    sections = []
    current_heading = "Introduction"
    current_content = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            # Count hashes
            header_match = re.match(r'^(#{1,6})\s+(.*)$', stripped)
            if header_match:
                if current_content:
                    text_block = "\n".join(current_content)
                    if text_block.strip():
                        sections.append({
                            "content": sanitize_text(text_block),
                            "section": current_heading,
                            "page_number": 1,
                            "version": global_version,
                            "last_updated": global_date
                        })
                    current_content = []
                current_heading = header_match.group(2).strip()
                continue
        current_content.append(line)

    if current_content:
        text_block = "\n".join(current_content)
        if text_block.strip():
            sections.append({
                "content": sanitize_text(text_block),
                "section": current_heading,
                "page_number": 1,
                "version": global_version,
                "last_updated": global_date
            })

    return sections

def parse_txt(file_path: str) -> List[Dict[str, Any]]:
    """Parse plain text, splitting by double newlines or uppercase headings."""
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    global_version, global_date = detect_version_and_date(text, filename)
    sections = []

    # Look for capitalized headers or divider lines
    paragraphs = re.split(r'\n{2,}', text)
    current_heading = "General"
    current_content = []

    for para in paragraphs:
        p_clean = para.strip()
        if not p_clean:
            continue
        # Check if single line heading
        lines = p_clean.splitlines()
        if len(lines) == 1 and (
            lines[0].isupper() or 
            lines[0].startswith("===") or 
            re.match(r'^(?:[0-9]+(?:\.[0-9]+)*\s+[A-Z]|SECTION|CHAPTER)', lines[0], re.IGNORECASE)
        ):
            if current_content:
                sections.append({
                    "content": sanitize_text("\n\n".join(current_content)),
                    "section": current_heading,
                    "page_number": 1,
                    "version": global_version,
                    "last_updated": global_date
                })
                current_content = []
            current_heading = lines[0].strip(" =#-:")
        else:
            current_content.append(p_clean)

    if current_content:
        sections.append({
            "content": sanitize_text("\n\n".join(current_content)),
            "section": current_heading,
            "page_number": 1,
            "version": global_version,
            "last_updated": global_date
        })

    return sections

def parse_document(file_path: str, doc_format: str) -> List[Dict[str, Any]]:
    doc_format = doc_format.lower().lstrip('.')
    if doc_format == "pdf":
        return parse_pdf(file_path)
    elif doc_format in ["html", "htm"]:
        return parse_html(file_path)
    elif doc_format in ["md", "markdown"]:
        return parse_markdown(file_path)
    elif doc_format in ["txt", "text"]:
        return parse_txt(file_path)
    else:
        # Default fallback to plain text parser
        return parse_txt(file_path)
