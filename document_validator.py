"""
Document validation module for Phase 4.
Implements schema-based validation and quarantine logic.
"""
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from document_processor import detect_file_type


class DocumentValidator:
    """Validates documents against schema templates."""
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.columns = schema.get('columns', [])
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def validate(self, parsed_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Validate parsed data against schema.
        Returns validation result with errors and warnings.
        """
        self.errors = []
        self.warnings = []
        
        # Check required fields
        for column in self.columns:
            if column.get('required', False):
                col_name = column.get('name', '').lower()
                if col_name in ['id', 'invoice_number', 'invoice_num', 'identifier']:
                    if 'id' not in parsed_data and 'invoice_number' not in parsed_data:
                        self.errors.append({
                            'field': 'id/invoice_number',
                            'column': column['name'],
                            'type': 'required',
                            'message': f"Required field '{column['name']}' not found in document"
                        })
                elif col_name in ['date', 'created_at', 'issue_date', 'timestamp']:
                    if 'date' not in parsed_data:
                        self.errors.append({
                            'field': 'date',
                            'column': column['name'],
                            'type': 'required',
                            'message': f"Required field '{column['name']}' not found in document"
                        })
                elif col_name in ['email']:
                    if 'email' not in parsed_data:
                        self.warnings.append({
                            'field': 'email',
                            'column': column['name'],
                            'type': 'missing',
                            'message': f"Optional field '{column['name']}' not found"
                        })
        
        # Validate data types
        for column in self.columns:
            col_name = column.get('name', '').lower()
            data_type = column.get('data_type', 'string').lower()
            
            if col_name in parsed_data:
                value = parsed_data[col_name]
                if data_type == 'number' and value is not None:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        self.errors.append({
                            'field': col_name,
                            'column': column['name'],
                            'type': 'invalid_type',
                            'expected': 'number',
                            'actual': type(value).__name__,
                            'message': f"Field '{column['name']}' should be a number"
                        })
                elif data_type == 'email' and value is not None:
                    if not self._is_valid_email(value):
                        self.errors.append({
                            'field': col_name,
                            'column': column['name'],
                            'type': 'invalid_format',
                            'expected': 'email',
                            'actual': value,
                            'message': f"Field '{column['name']}' is not a valid email"
                        })
                elif data_type == 'date' and value is not None:
                    if not self._is_valid_date(value):
                        self.errors.append({
                            'field': col_name,
                            'column': column['name'],
                            'type': 'invalid_format',
                            'expected': 'date',
                            'actual': value,
                            'message': f"Field '{column['name']}' is not a valid date"
                        })
        
        # Check for duplicate values
        if len(parsed_data) > 1:
            values = list(parsed_data.values())
            unique_values = set(str(v) for v in values if v is not None)
            if len(unique_values) < len(values):
                self.warnings.append({
                    'type': 'duplicate_values',
                    'message': "Document contains duplicate values"
                })
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'parsed_data': parsed_data,
            'validation_timestamp': datetime.now().isoformat()
        }
    
    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_date(self, date_str: str) -> bool:
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{2}/\d{2}/\d{4}$',
            r'^\d{2}-\d{2}-\d{4}$',
        ]
        for pattern in date_patterns:
            if re.match(pattern, date_str):
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    return True
                except ValueError:
                    pass
                try:
                    datetime.strptime(date_str, '%m/%d/%Y')
                    return True
                except ValueError:
                    pass
        return False


class QuarantineManager:
    """Manages quarantine zone for invalid documents."""
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = db_connection.cursor()
    
    def add_to_quarantine(self, document_id: int, validation_result: Dict[str, Any], 
                         reason: str = "Schema validation failed"):
        """Add document to quarantine zone."""
        self.cursor.execute('''
            UPDATE documents 
            SET status = 'quarantine', 
                quarantine_reason = ?,
                quarantine_notes = ?
            WHERE id = ?
        ''', (reason, validation_result.get('errors', []), document_id))
        self.conn.commit()
    
    def get_quarantined_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all quarantined documents."""
        self.cursor.execute('''
            SELECT d.*, s.name as schema_name, s.description as schema_description
            FROM documents d
            JOIN schemas s ON d.schema_id = s.id
            WHERE d.status = 'quarantine'
            ORDER BY d.created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def review_and_approve(self, document_id: int, corrected_data: Dict[str, Any]):
        """Review and approve a quarantined document."""
        self.cursor.execute('''
            UPDATE documents 
            SET status = 'validated',
                parsed_data = ?,
                reviewed_at = ?
            WHERE id = ?
        ''', (str(corrected_data), datetime.now().isoformat(), document_id))
        self.conn.commit()
    
    def reject(self, document_id: int, rejection_reason: str):
        """Reject a quarantined document."""
        self.cursor.execute('''
            UPDATE documents 
            SET status = 'error',
                error_message = ?
            WHERE id = ?
        ''', (rejection_reason, document_id))
        self.conn.commit()
    
    def get_document_status(self, document_id: int) -> Dict[str, Any]:
        """Get current status of a document."""
        self.cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def close(self):
        self.conn.close()
