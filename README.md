# Gemini-Style Chat Backend (FastAPI)

## Features
- OTP-based JWT authentication
- User-specific chatrooms
- AI chat via Gemini API
- Stripe subscription handling
- PostgreSQL & Redis integration

## Setup
1. Copy `.env.example` to `.env` and fill in your secrets.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the app:
   ```sh
   uvicorn app.main:app --reload
   ```

## Structure
- `app/` - FastAPI app code
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment variables
