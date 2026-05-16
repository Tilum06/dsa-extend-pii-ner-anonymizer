from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path

# Add parent directory to path to allow importing src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.regex_detector import detect_regex_entities
from src.context_detector import detect_by_context
from src.merger import merge_entities
from src.anonymizer import anonymize_text, build_token_entity_list

app = Flask(__name__)


@app.route("/")
def index():
    """Render main web interface."""
    return render_template("index.html")


@app.route("/api/detect", methods=["POST"])
def detect_pii():
    """
    API endpoint to detect and anonymize PII in text.

    Request JSON:
    {
        "text": "input text"
    }

    Response JSON:
    {
        "original_text": "original input",
        "anonymized_text": "text with PII masked",
        "entities": [
            {
                "type": "NAME",
                "text": "John Smith",
                "start": 11,
                "end": 22
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Step 1: Regex detection
        regex_entities = detect_regex_entities(text)

        # Step 2: Context detection
        context_entities = detect_by_context(text)

        # Step 3: Merge entities
        merged_entities = merge_entities(regex_entities, context_entities)

        # Step 4: Anonymize text
        anonymized_text = anonymize_text(text, merged_entities)

        # Format entities for response
        formatted_entities = [
            {
                "type": entity.get("type", "UNKNOWN"),
                "text": entity.get("text", ""),
                "start": entity.get("start", -1),
                "end": entity.get("end", -1),
            }
            for entity in merged_entities
        ]

        # Build token-level entity mapping
        token_entities = build_token_entity_list(text, merged_entities)

        return (
            jsonify(
                {
                    "original_text": text,
                    "anonymized_text": anonymized_text,
                    "entities": formatted_entities,
                    "token_entities": [
                        {"token": token, "label": label}
                        for token, label in token_entities
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
