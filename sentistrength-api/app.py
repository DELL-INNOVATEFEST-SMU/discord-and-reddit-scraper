from flask import Flask, request, jsonify
from sentistrength import PySentiStr
import os

app = Flask(__name__)

# Init SentiStrength
senti = PySentiStr()
senti.setSentiStrengthPath("/app/SentiStrength.jar")
senti.setSentiStrengthLanguageFolderPath("/app/SentiStrength_Data/")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400

    text_input = data["text"]
    if isinstance(text_input, str):
        text_input = [text_input]

    try:
        results = senti.getSentiment(text_input)
        return jsonify({"input": text_input, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "SentiStrength API is running"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
