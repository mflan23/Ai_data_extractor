import os
import json
import sqlite3
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from datetime import datetime
import aiosqlite
import tempfile

app = FastAPI(title="AI Dataset Builder API")

# Import validation endpoints
from validation_endpoints import (
    validate_document,
    get_quarantine_documents,
    review_quarantined_document,
    reject_quarantined_document,
    get_document_status
)

# Import AI config endpoints
from ai_config_endpoints import (
    get_current_config as ai_get_current_config,
    save_config as ai_save_config,
    reset_config as ai_reset_config
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "dataset_builder.db")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Schemas table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Columns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schema_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            data_type TEXT NOT NULL,
            required BOOLEAN DEFAULT 0,
            description TEXT,
            FOREIGN KEY (schema_id) REFERENCES schemas (id) ON DELETE CASCADE
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            schema_id INTEGER,
            status TEXT DEFAULT 'pending',
            raw_text TEXT,
            parsed_data TEXT,
            quarantine_reason TEXT,
            quarantine_notes TEXT,
            validated_at TIMESTAMP,
            reviewed_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (schema_id) REFERENCES schemas (id) ON DELETE SET NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    init_db()

# ============ Schema Routes ============

@app.post("/schemas")
async def create_schema(name: str, description: str = "", columns: List[Dict[str, Any]] = []):
    """Create a new schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO schemas (name, description) VALUES (?, ?)",
        (name, description)
    )
    schema_id = cursor.lastrowid
    
    for col in columns:
        cursor.execute(
            "INSERT INTO columns (schema_id, name, data_type, required, description) VALUES (?, ?, ?, ?, ?)",
            (schema_id, col['name'], col['data_type'], col.get('required', False), col.get('description', ''))
        )
    
    conn.commit()
    conn.close()
    
    return {"id": schema_id, "name": name, "description": description, "columns": columns}

@app.get("/schemas")
async def get_all_schemas():
    """Get all schemas"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM schemas ORDER BY created_at DESC")
    schemas = cursor.fetchall()
    
    result = []
    for schema in schemas:
        cursor.execute(
            "SELECT * FROM columns WHERE schema_id = ?",
            (schema['id'],)
        )
        columns = cursor.fetchall()
        
        result.append({
            "id": schema['id'],
            "name": schema['name'],
            "description": schema['description'],
            "columns": [dict(col) for col in columns],
            "created_at": schema['created_at']
        })
    
    conn.close()
    return result

@app.get("/schemas/{schema_id}")
async def get_schema(schema_id: int):
    """Get a specific schema by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM schemas WHERE id = ?", (schema_id,))
    schema = cursor.fetchone()
    
    if not schema:
        conn.close()
        raise HTTPException(status_code=404, detail="Schema not found")
    
    cursor.execute(
        "SELECT * FROM columns WHERE schema_id = ?",
        (schema_id,)
    )
    columns = cursor.fetchall()
    
    conn.close()
    return {
        "id": schema['id'],
        "name": schema['name'],
        "description": schema['description'],
        "columns": [dict(col) for col in columns],
        "created_at": schema['created_at']
    }

@app.delete("/schemas/{schema_id}")
async def delete_schema(schema_id: int):
    """Delete a schema and its columns"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM schemas WHERE id = ?", (schema_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Schema deleted successfully"}

# ============ Document Upload Routes ============

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), schema_id: str = Form(...)):
    """Upload a document for processing"""
    try:
        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file.filename)
        temp_file.close()
        
        contents = await file.read()
        with open(temp_file.name, 'wb') as f:
            f.write(contents)
        
        # Get schema
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schemas WHERE id = ?", (int(schema_id),))
        schema = cursor.fetchone()
        
        if not schema:
            conn.close()
            raise HTTPException(status_code=404, detail="Schema not found")
        
        # Insert document
        cursor.execute(
            "INSERT INTO documents (filename, filepath, schema_id, status) VALUES (?, ?, ?, ?)",
            (file.filename, temp_file.name, schema['id'], 'pending')
        )
        doc_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {
            "id": doc_id,
            "filename": file.filename,
            "schema_id": schema['id'],
            "status": "pending",
            "message": "Document uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_all_documents():
    """Get all documents"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    documents = cursor.fetchall()
    
    result = []
    for doc in documents:
        result.append({
            "id": doc['id'],
            "filename": doc['filename'],
            "filepath": doc['filepath'],
            "schema_id": doc['schema_id'],
            "status": doc['status'],
            "created_at": doc['created_at']
        })
    
    conn.close()
    return result

# ============ AI Routes ============

@app.post("/ai/suggestions")
async def get_ai_suggestions(context: Dict[str, Any]):
    """Get AI suggestions based on context"""
    if not is_ai_available():
        # Return mock suggestions
        suggestions = []
        if 'schemaName' in context:
            schema_name = context['schemaName'].lower()
            if 'invoice' in schema_name:
                suggestions = [
                    "Add 'Invoice Number' column for unique identification",
                    "Consider 'Issue Date' and 'Due Date' for tracking",
                    "Add 'Amount' and 'Tax Amount' for financial data",
                    "Include 'Payment Status' (Paid, Pending, Overdue)"
                ]
            elif 'customer' in schema_name:
                suggestions = [
                    "Add 'Email' and 'Phone' for contact information",
                    "Consider 'Customer Type' (B2B, B2C, VIP)",
                    "Add 'Registration Date' for tracking customer tenure",
                    "Include 'Preferred Contact Method'"
                ]
            else:
                suggestions = [
                    "Consider adding a unique identifier field",
                    "Add timestamps for created/updated dates",
                    "Include a status field for tracking"
                ]
        
        return {"suggestions": suggestions, "message": f"Analyzed schema: {context.get('schemaName', 'unknown')}", "provider": "mock"}
    
    # Use AI service
    result = ai_service.generate_suggestions(context)
    return result

@app.post("/ai/analyze-template")
async def analyze_template(file: UploadFile = File(...)):
    """Analyze a template file and generate schema"""
    # Read file content
    contents = await file.read()
    file_type = file.filename.lower()
    
    # Determine file type
    if file_type.endswith('.csv'):
        file_type = 'csv'
    elif file_type.endswith('.xlsx') or file_type.endswith('.xls'):
        file_type = 'excel'
    elif file_type.endswith('.json'):
        file_type = 'json'
    else:
        file_type = 'unknown'
    
    file_content = contents.decode('utf-8', errors='ignore')
    
    if not is_ai_available():
        # Return mock analysis
        return {
            "name": "Analyzed Template",
            "description": "Schema generated from template analysis",
            "columns": [
                {"name": "ID", "dataType": "number", "required": True},
                {"name": "Name", "dataType": "string", "required": True},
                {"name": "Email", "dataType": "email", "required": False},
                {"name": "Created At", "dataType": "date", "required": True},
            ],
            "suggestions": [
                "I noticed the 'Deadline' column contains mixed text and dates. Should we standardize this to a strict 'Date' format?",
                "Consider adding a 'Status' column to track record state",
                "The 'Name' field might benefit from being split into 'First Name' and 'Last Name'"
            ],
            "provider": "mock"
        }
    
    # Use AI service
    result = ai_service.analyze_template(file_content, file_type)
    return result

# ============ Validation Routes ============

@app.post("/documents/validate")
async def validate_document_endpoint(document_id: int):
    """Validate a document against its schema"""
    return await validate_document(document_id)

@app.get("/documents/quarantine")
async def get_quarantine_endpoint(limit: int = 100):
    """Get all quarantined documents"""
    return await get_quarantine_documents(limit)

@app.post("/documents/quarantine/review")
async def review_quarantine_endpoint(document_id: int, corrected_data: Dict[str, Any]):
    """Review and approve a quarantined document"""
    return await review_quarantined_document(document_id, corrected_data)

@app.post("/documents/quarantine/reject")
async def reject_quarantine_endpoint(document_id: int, rejection_reason: str):
    """Reject a quarantined document"""
    return await reject_quarantined_document(document_id, rejection_reason)

@app.get("/documents/status/{document_id}")
async def get_status_endpoint(document_id: int):
    """Get document status"""
    return await get_document_status(document_id)

# ============ AI Configuration Routes ============

@app.get("/ai-config/current")
async def get_ai_config():
    """Get current AI configuration"""
    return await ai_get_current_config()

@app.post("/ai-config/save")
async def save_ai_config():
    """Save AI configuration"""
    return await ai_save_config()

@app.post("/ai-config/reset")
async def reset_ai_config():
    """Reset AI configuration"""
    return await ai_reset_config()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
