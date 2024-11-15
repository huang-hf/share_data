from flask import Flask, request, jsonify
app = Flask(__name__)
@app.route("/api", methods=["POST"])
def api(): 
    return jsonify({"message": "Received", "data": request.json})
app.run(host="0.0.0.0", port=8080)
