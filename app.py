from flask import Flask, render_template, request, jsonify
from lexer import analyze

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def do_analyze():
    data = request.get_json()
    source = data.get("source", "")
    include_ws = data.get("include_whitespace", False)
    result = analyze(source, include_ws)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
