import os
import json
from flask import Flask, request, jsonify
from openai import OpenAI
from pyairtable import Api

app = Flask(__name__)

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
airtable_api = Api(os.environ.get("AIRTABLE_API_KEY"))
table = airtable_api.table(
    os.environ.get("AIRTABLE_BASE_ID"), 
    os.environ.get("AIRTABLE_TABLE_NAME")
)

@app.route('/webhook/call-completed', methods=['POST'])
def webhook():
    data = request.get_json() or {}
    print("--- INCOMING WEBHOOK ---")
    print(json.dumps(data, indent=2))

    call_data = data.get("call", {})
    transcript = call_data.get("transcript") or data.get("transcript")
    
    if not transcript:
        print("No transcript found in payload. Skipping Airtable write.")
        return jsonify({"status": "ignored_no_transcript"}), 200

    print("Extracting insights with OpenAI...")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI technical recruiter evaluating a candidate transcript. "
                        "Return ONLY a JSON object with these exact keys:\n"
                        "- Candidate ID: string (generate short ID like CAND-101 or extract name)\n"
                        "- Phone: string or null\n"
                        "- Overall Score: integer from 1 to 100\n"
                        "- Recommendation: string (Strong Hire, Hire, Consider, or Reject)\n"
                        "- Executive Summary: string (2-3 sentences summarising candidate fit)\n"
                        "- Technical Depth: string (detailed assessment of technical skills)"
                    )
                },
                {"role": "user", "content": f"Transcript:\n{transcript}"}
            ],
            response_format={"type": "json_object"}
        )

        extracted_data = json.loads(response.choices[0].message.content)
        print("OpenAI Output:", extracted_data)

        record = {
            "Candidate ID": str(extracted_data.get("Candidate ID", "CAND-001")),
            "Phone": str(call_data.get("from_number", "N/A")),
            "Overall Score": int(extracted_data.get("Overall Score", 75)),
            "Recommendation": str(extracted_data.get("Recommendation", "Consider")),
            "Executive Summary": str(extracted_data.get("Executive Summary", "")),
            "Technical Depth": str(extracted_data.get("Technical Depth", ""))
        }

        print("Writing record to Airtable...")
        created = table.create(record)
        print("Successfully created Airtable record:", created["id"])

        return jsonify({"status": "success", "airtable_id": created["id"]}), 200

    except Exception as e:
        print("ERROR processing call:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
