# Social Media Automation Service

A Python microservice that fully replaces the n8n automation workflow for social media posting. It supports multi-provider AI content generation (OpenAI, Gemini, OpenRouter) and multi-account posting via Make.com webhooks.

## 📁 Project Structure
The project is organized for maximum simplicity and modularity:
- **`app/agent/`**: Consolidated application logic and infrastructure.
  - `app.py`: The main orchestrator and scheduler.
  - `config.py`: Configuration management.
  - `airtable_client.py`: Robust Airtable record management.
  - `creator.py`: Multi-provider AI content generation.
  - `media_modifier.py`: Metadata modification via AWS Lambda.
  - `poster.py`: Multi-channel dispatch via Make.com webhooks.
  - `Dockerfile`, `docker-compose.yml`, `.env`, `requirements.txt`.

## 🚀 Full Local Setup
1. Ensure you have Python 3.10+ installed.
2. Clone this repository or open the project folder.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ .env Configuration
Create a `.env` file and fill in your credentials:
```env
AIRTABLE_API_KEY=your_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_NAME=your_table_name

# AI Provider Settings
LLM_PROVIDER=openai  # 'openai', 'gemini', or 'openrouter'
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key

# Webhooks & Media
MAKE_WEBHOOK_URL=your_default_webhook
IMAGE_METADATA_API=your_lambda_url
VIDEO_METADATA_API=your_lambda_url
```

## 🏃 How to Run
### Directly via Python:
```bash
cd app/agent
python app.py
```
The application will execute pending posts immediately on startup and then follow the 8:00 PM IST schedule (Monday-Saturday).

### Via Docker:
1. Build and start:
   ```bash
   cd app/agent
   docker-compose up -d --build
   ```
2. Inspect logs:
   ```bash
   cd app/agent
   docker-compose logs -f
   ```

## 🛡️ Key Features
- **Redundancy & Retries**: Only marks records as "Done" if all platforms and accounts succeed.
- **Smart Parsing**: Custom regex parser for AI outputs to prevent data loss from formatting errors.
- **Rate Limiting**: Built-in delays to respect social platform and API limits.
- **Stateless Design**: Fully driven by Airtable as the source of truth.