"""
PDF parsing utility for extracting guidelines
"""
import pdfplumber
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger


class PDFParser:
    """Extract text and structure from PDF guidelines"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    def extract_text(self) -> str:
        """Extract all text from PDF"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text_pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_pages.append(text)
                
                full_text = "\n\n".join(text_pages)
                logger.info(f"Extracted {len(full_text)} characters from {len(text_pages)} pages")
                return full_text
                
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
    
    def extract_structured(self) -> Dict[str, Any]:
        """
        Extract structured information including tables
        
        Returns:
            Dictionary with text, tables, and metadata
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                data = {
                    "text": "",
                    "tables": [],
                    "metadata": {},
                    "pages": len(pdf.pages)
                }
                
                # Extract metadata
                if pdf.metadata:
                    data["metadata"] = {
                        "title": pdf.metadata.get("Title", ""),
                        "author": pdf.metadata.get("Author", ""),
                        "subject": pdf.metadata.get("Subject", "")
                    }
                
                # Extract text and tables from each page
                all_text = []
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        data["tables"].append({
                            "page": page_num,
                            "data": table
                        })
                
                data["text"] = "\n\n".join(all_text)
                
                logger.success(f"Extracted structured data: {data['pages']} pages, {len(data['tables'])} tables")
                return data
                
        except Exception as e:
            logger.error(f"Structured extraction failed: {e}")
            raise
    
    def extract_formatting_rules(self) -> List[str]:
        """
        Extract key formatting rules from text
        Looks for patterns like margins, fonts, spacing
        """
        text = self.extract_text()
        
        rules = []
        keywords = [
            "margin", "font", "spacing", "size", "style", 
            "alignment", "indent", "bold", "italic",
            "header", "footer", "page number"
        ]
        
        lines = text.split("\n")
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                rules.append(line.strip())
        
        logger.info(f"Extracted {len(rules)} formatting rules")
        return rules


def parse_guidelines_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse guidelines PDF
    
    Returns:
        Full structured data including text and tables
    """
    parser = PDFParser(pdf_path)
    return parser.extract_structured()
