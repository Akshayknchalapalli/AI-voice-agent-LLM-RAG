$env:SUPABASE_URL = "https://adjeevevdefynqguhbma.supabase.co"
$env:SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFkamVldmV2ZGVmeW5xZ3VoYm1hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQwMzk4OTEsImV4cCI6MjA1OTYxNTg5MX0.VR1CVNde-ohAUXokma5qTportJbOXm-8b-tRxiObl5I"

& "C:\Users\Akshay k\Desktop\AI-voice-agent-LLM-RAG\.venv\Scripts\Activate.ps1"
pytest tests/services/db/test_supabase_service.py -v --log-cli-level=INFO
