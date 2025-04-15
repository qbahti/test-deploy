from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import random

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", subjects=["Информатика", "Қазақстан тарихы"], error=None)

@app.route("/start", methods=["POST"])
def start():
    name = request.form.get("name")
    subject = request.form.get("subject")
    access_code = request.form.get("access_code")

    correct_codes = {
        "Информатика": "inf2024",
        "Қазақстан тарихы": "tar2024"
    }

    if correct_codes.get(subject) != access_code:
        return render_template("index.html", subjects=correct_codes.keys(), error="Құпия код дұрыс емес!")

    # Пәнге байланысты сұрақ базасын таңдау
    if subject == "Информатика":
        filename = "data/questions_informatika.json"
    elif subject == "Қазақстан тарихы":
        filename = "data/questions_tarikh.json"
    else:
        return redirect(url_for("index"))

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = min(30, len(data["single"]))
    questions = random.sample(data["single"], count)
    return render_template("test.html", name=name, subject=subject, questions={"single": questions})

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    name = data.get("name")
    subject = data.get("subject")
    score = data.get("score")
    answers = data.get("answers")

    return jsonify({
        "redirect": url_for("result", name=name, subject=subject, score=score)
    })

@app.route("/result")
def result():
    name = request.args.get("name")
    subject = request.args.get("subject")
    score = request.args.get("score")
    return render_template("result.html", name=name, subject=subject, score=score)

if __name__ == "__main__":
    app.run(debug=True)