"""
Validation endpoints for Phase 4.
Handles document validation and quarantine management.
"""
import os
import sqlite3
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from document_validator import DocumentValidator, QuarantineManager
from ai_service import get_ai_service, AIService
from ai_config import AIConfig, AIProvider, is_ai_available

app = FastAPI()

DB_PATH = os.path.join(os.path.dirname(__file__), "dataset_builder.db")

# Initialize AI config and service
ai_config = AIConfig.from_env()
ai_service = get_ai_service(ai_config)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.post("/documents/validate")
async def validate_document(document_id: int):
    """
    Validate a document against its schema.
    Returns validation result and updates document status.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get document and schema
    cursor.execute('''
        SELECT d.*, s.name as schema_name, s.description as schema_description
        FROM documents d
        JOIN schemas s ON d.schema_id = s.id
        WHERE d.id = ?
    ''', (document_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = dict(row)
    schema = {
        'name': document['schema_name'],
        'description': document['schema_description'],
        'columns': []
    }
    
    # Get schema columns
    cursor.execute('''
        SELECT * FROM columns WHERE schema_id = ?
    ''', (document['schema_id'],))
    columns = cursor.fetchall()
    for col in columns:
        schema['columns'].append({
            'name': col['name'],
            'data_type': col['data_type'],
            'required': bool(col['required']),
            'description': col.get('description', '')
        })
    
    conn.close()
    
    # Validate document
    validator = DocumentValidator(schema)
    
    # Parse document text (placeholder - should use existing parser)
    parsed_data = {
        'id': document.get('parsed_data', {}).get('id', ''),
        'invoice_number': document.get('parsed_data', {}).get('invoice_number', ''),
        'date': document.get('parsed_data', {}).get('date', ''),
        'email': document.get('parsed_data', {}).get('email', ''),
        'amount': document.get('parsed_data', {}).get('amount', ''),
    }
    
    validation_result = validator.validate(parsed_data, document.get('raw_text', ''))
    
    # Update document status
    if validation_result['valid']:
        status = 'validated'
        message = "Document validated successfully"
    else:
        status = 'quarantine'
        message = f"Document quarantined: {len(validation_result['errors'])} errors found"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE documents 
        SET status = ?,
            parsed_data = ?,
            validated_at = ?
        WHERE id = ?
    ''', (
        status,
        str(validation_result['parsed_data']),
        datetime.now().isoformat(),
        document_id
    ))
    conn.commit()
    conn.close()
    
    return {
        'document_id': document_id,
        'status': status,
        'message': message,
        'validation_result': validation_result
    }


@app.get("/documents/quarantine")
async def get_quarantine_documents(limit: int = 100):
    """Get all quarantined documents."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.*, s.name as schema_name, s.description as schema_description
        FROM documents d
        JOIN schemas s ON d.schema_id = s.id
        WHERE d.status = 'quarantine'
        ORDER BY d.created_at DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    documents = []
    for row in rows:
        documents.append({
            'id': row['id'],
            'filename': row['filename'],
            'filepath': row['filepath'],
            'schema_id': row['schema_id'],
            'schema_name': row['schema_name'],
            'schema_description': row['schema_description'],
            'status': row['status'],
            'quarantine_reason': row.get('quarantine_reason', ''),
            'quarantine_notes': row.get('quarantine_notes', ''),
            'created_at': row['created_at'],
            'validated_at': row.get('validated_at'),
            'reviewed_at': row.get('reviewed_at')
        })
    
    conn.close()
    return {'documents': documents, 'count': len(documents)}


@app.post("/documents/quarantine/review")
async def review_quarantined_document(document_id: int, corrected_data: Dict[str, Any]):
    """Review and approve a quarantined document."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get document
    cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update document status to validated
    cursor.execute('''
        UPDATE documents 
        SET status = 'validated',
            parsed_data = ?,
            reviewed_at = ?
        WHERE id = ?
    ''', (str(corrected_data), datetime.now().isoformat(), document_id))
    conn.commit()
    
    conn.close()
    return {
        'document_id': document_id,
        'status': 'validated',
        'message': 'Document approved and moved to validated queue'
    }


@app.post("/documents/quarantine/reject")
async def reject_quarantined_document(document_id: int, rejection_reason: str):
    """Reject a quarantined document."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get document
    cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update document status to error
    cursor.execute('''
        UPDATE documents 
        SET status = 'error',
            error_message = ?
        WHERE id = ?
    ''', (rejection_reason, document_id))
    conn.commit()
    
    conn.close()
    return {
        'document_id': document_id,
        'status': 'error',
        'message': 'Document rejected'
    }


@app.get("/documents/status/{document_id}")
async def get_document_status(document_id: int):
    """Get current status of a document."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = dict(row)
    conn.close()
    
    return document
