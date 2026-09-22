import os
import json
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Candidates")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_EVALUATION_PROMPT = """
You are an expert technical interviewer evaluating a candidate's transcript.
Analyze the transcript against this rubric:
1. Technical Depth (35%): Architectural mastery, tool choices, edge case awareness.
2. Problem Solving (30%): Systems thinking, scalability, cost trade-offs.
3. Project Ownership (20%): Leadership, decision autonomy, business impact metrics.
4. Communication (15%): Clarity, conciseness, non-technical translation.

Output ONLY valid JSON matching this schema:
{
  "candidate_id": "STRING",
  "overall_score": FLOAT,
  "match_recommendation": "STRONG_HIRE" | "HIRE" | "NEUTRAL" | "REJECT",
  "executive_summary": "STRING",
  "scores": {
    "technical_depth": {"score": INT, "reasoning": "STRING"},
    "problem_solving": {"score": INT, "reasoning": "STRING"},
    "project_ownership": {"score": INT, "reasoning": "STRING"},
    "communication": {"score": INT, "reasoning": "STRING"}
  },
  "extracted_skills": ["STRING"],
  "key_quotes": ["STRING"]
}
"""

@app.route("/webhook/call-completed", methods=["POST"])
def handle_call_completed():
    data = request.get_json()
    call_data = data.get("message", data)
    transcript = call_data.get("transcript", "")
    candidate_phone = call_data.get("customer", {}).get("number", "N/A")
    call_id = call_data.get("id", "UNKNOWN_CALL")

    if not transcript:
        return jsonify({"status": "ignored", "reason": "empty transcript"}), 200

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_EVALUATION_PROMPT},
            {"role": "user", "content": f"Candidate Phone: {candidate_phone}\nTranscript:\n{transcript}"}
        ],
        temperature=0.2
    )

    eval_result = json.loads(response.choices[0].message.content)

    airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "records": [
            {
                "fields": {
                    "Candidate ID": eval_result.get("candidate_id", call_id),
                    "Phone": candidate_phone,
                    "Overall Score": eval_result.get("overall_score"),
                    "Recommendation": eval_result.get("match_recommendation"),
                    "Executive Summary": eval_result.get("executive_summary"),
                    "Technical Depth Score": eval_result["scores"]["technical_depth"]["score"],
                    "Problem Solving Score": eval_result["scores"]["problem_solving"]["score"],
                    "Ownership Score": eval_result["scores"]["project_ownership"]["score"],
                    "Communication Score": eval_result["scores"]["communication"]["score"],
                    "Skills": ", ".join(eval_result.get("extracted_skills", [])),
                    "Transcript": transcript
                }
            }
        ]
    }

    airtable_res = requests.post(airtable_url, headers=headers, json=payload)
    return jsonify({"status": "success", "airtable_id": airtable_res.json()}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
