# API Reference Documentation

## Authentication Endpoints

### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123"
}
```

**Response:** Returns JWT access token and user profile.

### POST /api/auth/login
Authenticate with email and password.

### GET /api/auth/me
Get current user profile. Requires valid JWT token.

## Document Endpoints

### POST /api/documents/upload
Upload a document for processing. Accepts PDF, DOCX, TXT, and Markdown files.

Maximum file size: 50MB.

### GET /api/documents/
List all documents with pagination and filtering.

Query parameters:
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20)
- `status` (string): Filter by processing status
- `search` (string): Search by filename

### GET /api/documents/{id}
Get document details by ID.

### DELETE /api/documents/{id}
Delete a document and all associated data.

## Q&A Endpoints

### POST /api/ask
Ask a question about uploaded documents.

**Request Body:**
```json
{
  "question": "What is the system architecture?",
  "conversation_id": null,
  "document_ids": null
}
```

**Response:**
```json
{
  "answer": "The system uses a three-tier architecture...",
  "citations": [
    {
      "citation_label": "[S1]",
      "filename": "architecture_guide.md",
      "page_number": 1,
      "excerpt": "..."
    }
  ],
  "insufficient_evidence": false,
  "latency_breakdown": {
    "total_ms": 1200,
    "retrieval_ms": 200,
    "generation_ms": 1000
  }
}
```

## Configuration

The API server runs on port 8000 by default. Configure using environment variables in `.env`.

Database connection string format: `postgresql+asyncpg://user:pass@host:port/dbname`
