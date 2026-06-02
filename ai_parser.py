"""
AI Parsing Service
Parses extracted text according to a schema template and returns structured JSON data.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class AIParser:
    """
    AI-powered document parser that extracts data according to schema templates.
    Uses pattern matching and heuristics to map raw text to schema fields.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize parser with schema template.
        
        Args:
            schema: Schema definition with columns
        """
        self.schema = schema
        self.columns = schema.get('columns', [])
        self.data = {}
    
    def parse(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse raw text according to schema template.
        
        Args:
            raw_text: Extracted text from document
            
        Returns:
            Parsed data dictionary
        """
        self.data = {'_raw_text': raw_text, '_parsed_at': datetime.now().isoformat()}
        
        for column in self.columns:
            col_name = column.get('name', '').lower()
            col_type = column.get('data_type', 'string').lower()
            
            # Apply column-specific parsing logic
            if col_name in ['id', 'invoice_number', 'invoice_num', 'doc_number']:
                self.data[column['name']] = self._extract_id(raw_text)
            elif col_name in ['date', 'created_at', 'issue_date', 'due_date']:
                self.data[column['name']] = self._extract_date(raw_text)
            elif col_name in ['email']:
                self.data[column['name']] = self._extract_email(raw_text)
            elif col_name in ['phone', 'telephone']:
                self.data[column['name']] = self._extract_phone(raw_text)
            elif col_name in ['amount', 'total', 'price']:
                self.data[column['name']] = self._extract_number(raw_text)
            elif col_name in ['boolean', 'is_active', 'status']:
                self.data[column['name']] = self._extract_boolean(raw_text)
            else:
                # Default: extract as string
                self.data[column['name']] = self._extract_string(raw_text, col_name)
        
        return self.data
    
    def _extract_id(self, text: str) -> Optional[str]:
        """Extract ID or invoice number from text"""
        patterns = [
            r'Invoice\s*#?\s*(\d+)',
            r'Invoice\s*Number[:\s]*(\d+)',
            r'Doc\s*#?\s*(\d+)',
            r'Reference\s*#?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try to find any numeric ID
        numbers = re.findall(r'\b\d{4,}\b', text)
        if numbers:
            return numbers[0]
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Normalize to ISO format
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        # MM/DD/YYYY -> YYYY-MM-DD
                        return f"{parts[2]}-{parts[0]}-{parts[1]}"
                return date_str
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        phone_patterns = [
            r'\+?1?\s?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        # Look for currency amounts
        currency_pattern = r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(currency_pattern, text)
        
        if match:
            return float(match.group(1).replace(',', ''))
        
        return None
    
    def _extract_boolean(self, text: str) -> Optional[bool]:
        """Extract boolean value from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['yes', 'true', 'paid', 'active', 'completed']):
            return True
        elif any(word in text_lower for word in ['no', 'false', 'unpaid', 'inactive', 'pending']):
            return False
        
        return None
    
    def _extract_string(self, text: str, column_name: str) -> Optional[str]:
        """
        Extract string value based on column name heuristics.
        """
        # Look for common patterns based on column name
        if 'name' in column_name.lower():
            # Try to find "Name:" or similar
            pattern = r'(?:Name|Customer|Client)[:\s]+([A-Za-z\s]+?)(?:\n|$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        elif 'address' in column_name.lower():
            # Try to find address block
            pattern = r'(?:Address)[:\s]+([A-Za-z0-9,\s#]+?)(?:\n\n|$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        elif 'description' in column_name.lower():
            # Extract text between description markers
            pattern = r'(?:Description|Notes)[:\s]+(.+?)(?:\n\n|$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: return first line of text
        lines = text.split('\n')
        if lines:
            return lines[0].strip()
        
        return None
    
    def get_validation_errors(self) -> List[str]:
        """
        Check for validation errors in parsed data.
        """
        errors = []
        
        for column in self.columns:
            col_name = column.get('name', '')
            col_type = column.get('data_type', 'string').lower()
            required = column.get('required', False)
            
            value = self.data.get(col_name)
            
            if required and not value:
                errors.append(f"Missing required field: {col_name}")
            
            # Type validation
            if value is not None:
                if col_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Invalid type for {col_name}: expected number, got {type(value).__name__}")
                elif col_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Invalid type for {col_name}: expected boolean, got {type(value).__name__}")
        
        return errors


def parse_document_with_schema(raw_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to parse document text with schema.
    
    Args:
        raw_text: Extracted text from document
        schema: Schema definition
        
    Returns:
        Dictionary with parsed data and validation results
    """
    parser = AIParser(schema)
    parsed_data = parser.parse(raw_text)
    errors = parser.get_validation_errors()
    
    return {
        'parsed_data': parsed_data,
        'validation_errors': errors,
        'is_valid': len(errors) == 0
    }


if __name__ == "__main__":
    # Test the parser
    test_schema = {
        'name': 'Test Invoice',
        'columns': [
            {'name': 'Invoice Number', 'data_type': 'string', 'required': True},
            {'name': 'Date', 'data_type': 'date', 'required': True},
            {'name': 'Amount', 'data_type': 'number', 'required': True},
            {'name': 'Customer Name', 'data_type': 'string', 'required': False},
        ]
    }
    
    test_text = """
    Invoice #12345
    Date: 01/15/2026
    
    Customer Name: John Doe
    Amount: $1,250.00
    
    Description: Professional services
    """
    
    result = parse_document_with_schema(test_text, test_schema)
    print(f"Parsed data: {result['parsed_data']}")
    print(f"Validation errors: {result['validation_errors']}")
