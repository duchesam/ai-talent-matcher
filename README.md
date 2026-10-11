# AI Talent Matcher

An interview evidence workspace by Ermias Seyoum, built with Flask, OpenAI, Airtable, and Render.

## Browser demo

Visit https://ai-talent-matcher-nepk.onrender.com after deployment. The homepage uses fictional examples, browser-local keyword extraction, search, sample reset, and a downloadable evidence brief. No private candidate records or paid model calls are exposed through the demo. It does not score, rank, or make hiring recommendations.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server.py
```

Open http://localhost:10000. Test with `.venv/bin/python -m unittest test_server.py`.

## Render configuration

Build: `pip install -r requirements.txt`

Start: `gunicorn server:app --bind 0.0.0.0:$PORT --timeout 90`

Health check: `/health`

The homepage and health check work without credentials. Integration clients are initialized only when an authenticated webhook is processed. `pyairtable` is included in the dependency list to fix the missing import in the previous deployment.

## Private webhook integration

Set OPENAI_API_KEY, AIRTABLE_API_KEY (Airtable personal access token), AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, and a strong WEBHOOK_SECRET in Render environment settings. Do not put credentials in source control. Optional OPENAI_MODEL defaults to gpt-4o.

Configure the trusted webhook sender to include `Authorization: Bearer <WEBHOOK_SECRET>` when POSTing JSON to `/webhook/call-completed`. Without a configured secret the endpoint returns 503; invalid authentication returns 401. Existing senders must be updated to include authentication.

Accepts `call.transcript`, `message.transcript`, or top-level `transcript`. The integration summarizes factual technical evidence for human review and stores Candidate ID, Executive Summary, and Technical Depth in Airtable. Ensure these text fields exist. Former score and hire/reject recommendation fields are no longer written. Transcripts and contact details are not logged or publicly listed.

This demo is not a production recruiting system. Durable webhook idempotency, provider-specific signature verification, retention controls, access management, monitoring, and expanded integration testing remain deployment work. Verify model summaries before using them.
