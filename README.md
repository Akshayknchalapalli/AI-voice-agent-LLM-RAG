# Real Estate AI Voice Agent

An intelligent voice agent system for real estate that handles property inquiries, recommendations, and lead management using advanced AI capabilities.

## Features

- Voice and WebRTC-based communication
- Natural language processing with LLM integration
- Property recommendation engine
- Lead management system
- Admin dashboard for monitoring and configuration

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, LangChain, LlamaIndex
- **Voice Processing**: Twilio, LiveKit, Deepgram/Whisper, ElevenLabs
- **Database**: PostgreSQL, Pinecone/Weaviate, Redis
- **Frontend**: React 18, TypeScript, Material-UI
- **Infrastructure**: Docker, Kubernetes

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`
4. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Project Structure

```
.
├── app/
│   ├── api/            # API routes
│   ├── core/           # Core application logic
│   ├── models/         # Database models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic services
│   └── utils/          # Utility functions
├── frontend/          # React frontend application
├── tests/            # Test cases
└── docker/           # Docker configuration
```

## Environment Variables

Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
OPENAI_API_KEY=your_key
PINECONE_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
```

## License

MIT
