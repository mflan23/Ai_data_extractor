"""
AI Service for generating schema suggestions and analyzing templates.
Supports multiple AI providers with API key authentication.
"""
import os
import re
from typing import Dict, Any, List, Optional
from ai_config import AIConfig, AIProvider, is_ai_available, get_current_provider, get_current_model, update_config


class AIService:
    """Service for AI-powered schema generation and analysis."""
    
    def __init__(self, config: AIConfig):
        self.config = config
    
    def generate_suggestions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI suggestions based on schema context.
        Returns structured suggestions with explanations.
        """
        if not is_ai_available():
            return self._get_mock_suggestions(context)
        
        try:
            # Build prompt based on context
            prompt = self._build_suggestion_prompt(context)
            
            # Call AI API
            response = self._call_ai_api(prompt, "suggestions")
            
            # Parse response
            suggestions = self._parse_suggestions_response(response)
            
            return {
                "suggestions": suggestions,
                "provider": get_current_provider(),
                "model": get_current_model(),
                "message": f"Generated {len(suggestions)} suggestions using {get_current_provider()}"
            }
            
        except Exception as e:
            print(f"AI suggestion error: {str(e)}")
            return self._get_mock_suggestions(context)
    
    def analyze_template(self, file_content: str, file_type: str) -> Dict[str, Any]:
        """
        Analyze a template file and generate schema suggestions.
        """
        if not is_ai_available():
            return self._get_mock_template_analysis()
        
        try:
            prompt = self._build_analysis_prompt(file_content, file_type)
            response = self._call_ai_api(prompt, "analysis")
            
            schema = self._parse_schema_response(response)
            suggestions = self._parse_suggestions_response(response)
            
            return {
                "name": "AI-Generated Schema",
                "description": f"Schema generated from {file_type} template analysis",
                "columns": schema.get("columns", []),
                "suggestions": suggestions,
                "provider": get_current_provider(),
                "model": get_current_model()
            }
            
        except Exception as e:
            print(f"Template analysis error: {str(e)}")
            return self._get_mock_template_analysis()
    
    def _build_suggestion_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for generating schema suggestions."""
        schema_name = context.get('schemaName', 'unknown')
        column_names = context.get('columnNames', [])
        
        prompt = f"""You are an expert data architect. Analyze the following schema context and provide intelligent suggestions for improvement:

Schema Name: {schema_name}
Existing Columns: {', '.join(column_names) if column_names else 'None defined yet'}

Please provide specific, actionable suggestions for:
1. Missing critical fields
2. Data type improvements
3. Validation rules
4. Best practices for this type of data

Format your response as a JSON array of suggestion objects with:
- suggestion: The suggestion text
- reason: Why this suggestion is important
- priority: "high", "medium", or "low"
- example: An example value or format if applicable

Return ONLY valid JSON, no markdown formatting."""
        
        return prompt
    
    def _build_analysis_prompt(self, file_content: str, file_type: str) -> str:
        """Build prompt for template analysis."""
        prompt = f"""You are an expert data architect. Analyze the following {file_type} template content and extract schema information:

Template Content:
{file_content[:2000]}

Extract the following information:
1. Column names and their purposes
2. Data types for each column
3. Which columns are required vs optional
4. Any patterns or constraints observed

Return your analysis as a JSON object with:
- name: Suggested schema name
- description: Brief description
- columns: Array of column objects with name, dataType, required, description
- suggestions: Array of improvement suggestions

Return ONLY valid JSON, no markdown formatting."""
        
        return prompt
    
    def _call_ai_api(self, prompt: str, task_type: str) -> Dict[str, Any]:
        """Call the AI API with the given prompt."""
        import httpx
        
        headers = self.config.get_headers()
        
        if self.config.provider == AIProvider.OPENAI:
            return self._call_openai(prompt, task_type, headers)
        elif self.config.provider == AIProvider.ANTHROPIC:
            return self._call_anthropic(prompt, task_type, headers)
        elif self.config.provider == AIProvider.GOOGLE_GEMINI:
            return self._call_gemini(prompt, task_type, headers)
        elif self.config.provider == AIProvider.LOCAL:
            return self._call_local_ai(prompt, task_type)
        
        raise ValueError(f"Unknown provider: {self.config.provider}")
    
    def _call_openai(self, prompt: str, task_type: str, headers: Dict) -> Dict[str, Any]:
        """Call OpenAI API."""
        import httpx
        
        url = "https://api.openai.com/v1/chat/completions"
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "success": True
                }
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _call_anthropic(self, prompt: str, task_type: str, headers: Dict) -> Dict[str, Any]:
        """Call Anthropic API."""
        import httpx
        
        url = "https://api.anthropic.com/v1/messages"
        
        payload = {
            "model": self.config.model,
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "system": "You are a helpful AI assistant."
        }
        
        try:
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                return {
                    "content": result["content"][0]["text"],
                    "success": True
                }
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _call_gemini(self, prompt: str, task_type: str, headers: Dict) -> Dict[str, Any]:
        """Call Google Gemini API."""
        import httpx
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/:generateContent"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"System: You are a helpful AI assistant.\nUser: {prompt}"}
                    ]
                }
            ]
        }
        
        try:
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(url.replace(":", self.config.model), json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                return {
                    "content": result["candidates"][0]["content"]["parts"][0]["text"],
                    "success": True
                }
        except Exception as e:
            raise Exception(f"Google Gemini API error: {str(e)}")
    
    def _call_local_ai(self, prompt: str, task_type: str) -> Dict[str, Any]:
        """Call local AI model (Ollama, LM Studio, etc.)."""
        import httpx
        
        url = f"{self.config.base_url}/api/chat"
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        
        try:
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return {
                    "content": result.get("message", {}).get("content", ""),
                    "success": True
                }
        except Exception as e:
            raise Exception(f"Local AI error: {str(e)}")
    
    def _parse_suggestions_response(self, response: Dict[str, Any]) -> List[str]:
        """Parse AI response into structured suggestions."""
        content = response.get("content", "")
        
        # Try to parse as JSON
        try:
            import json
            data = json.loads(content)
            if isinstance(data, list):
                return [s.get("suggestion", s) if isinstance(s, dict) else s for s in data]
            elif isinstance(data, dict) and "suggestions" in data:
                return data["suggestions"]
        except json.JSONDecodeError:
            pass
        
        # Fallback: extract suggestions from text
        suggestions = []
        # Simple extraction based on common patterns
        if "suggestion" in content.lower():
            suggestions = content.split("\n")[:5]
        
        return suggestions if suggestions else ["No suggestions generated"]
    
    def _parse_schema_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response into schema structure."""
        content = response.get("content", "")
        
        try:
            import json
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "name": "AI-Generated Schema",
                "description": "Schema generated from template analysis",
                "columns": [
                    {"name": "ID", "dataType": "number", "required": True},
                    {"name": "Name", "dataType": "string", "required": True},
                    {"name": "Created At", "dataType": "date", "required": True}
                ]
            }
    
    def _get_mock_suggestions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock suggestions when AI is not available."""
        suggestions = []
        
        schema_name = context.get('schemaName', '').lower()
        
        if 'invoice' in schema_name:
            suggestions = [
                {"suggestion": "Add 'Invoice Number' column for unique identification", "reason": "Essential for tracking and referencing", "priority": "high", "example": "INV-2024-001"},
                {"suggestion": "Consider 'Issue Date' and 'Due Date' for tracking", "reason": "Important for payment cycles", "priority": "high", "example": "2024-01-15"},
                {"suggestion": "Add 'Amount' and 'Tax Amount' for financial data", "reason": "Critical for accounting", "priority": "high", "example": "$1,250.00"},
                {"suggestion": "Include 'Payment Status' (Paid, Pending, Overdue)", "reason": "Track invoice lifecycle", "priority": "medium", "example": "Paid"}
            ]
        elif 'customer' in schema_name:
            suggestions = [
                {"suggestion": "Add 'Email' and 'Phone' for contact information", "reason": "Essential for communication", "priority": "high", "example": "customer@example.com"},
                {"suggestion": "Consider 'Customer Type' (B2B, B2C, VIP)", "reason": "Segment customers for targeting", "priority": "medium", "example": "B2B"},
                {"suggestion": "Add 'Registration Date' for tracking customer tenure", "reason": "Analyze customer lifetime value", "priority": "medium", "example": "2023-06-15"},
                {"suggestion": "Include 'Preferred Contact Method'", "reason": "Improve communication effectiveness", "priority": "low", "example": "Email"}
            ]
        else:
            suggestions = [
                {"suggestion": "Consider adding a unique identifier field", "reason": "Essential for data integrity", "priority": "high", "example": "UUID or auto-increment ID"},
                {"suggestion": "Add timestamps for created/updated dates", "reason": "Track data lifecycle", "priority": "medium", "example": "Created: 2024-01-15, Updated: 2024-06-01"},
                {"suggestion": "Include a status field for tracking", "reason": "Monitor data state", "priority": "medium", "example": "Active, Inactive, Archived"}
            ]
        
        return {
            "suggestions": [s["suggestion"] for s in suggestions],
            "provider": "mock",
            "model": "mock",
            "message": f"Generated {len(suggestions)} mock suggestions"
        }
    
    def _get_mock_template_analysis(self) -> Dict[str, Any]:
        """Return mock template analysis when AI is not available."""
        return {
            "name": "AI-Generated Schema",
            "description": "Schema generated from template analysis",
            "columns": [
                {"name": "ID", "dataType": "number", "required": True},
                {"name": "Name", "dataType": "string", "required": True},
                {"name": "Email", "dataType": "email", "required": False},
                {"name": "Created At", "dataType": "date", "required": True}
            ],
            "suggestions": [
                "I noticed the 'Deadline' column contains mixed text and dates. Should we standardize this to a strict 'Date' format?",
                "Consider adding a 'Status' column to track record state",
                "The 'Name' field might benefit from being split into 'First Name' and 'Last Name'"
            ],
            "provider": "mock",
            "model": "mock"
        }


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service(config: AIConfig) -> AIService:
    """Get or create AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService(config)
    return _ai_service
