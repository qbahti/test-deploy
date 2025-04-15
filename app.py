from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'any_secret_key'  # сессия үшін міндетті

# Пән тізімі
SUBJECTS = ['Информатика', 'Қазақстан тарихы']

# Басты бет
@app.route('/')
def index():
    return render_template('index.html', subjects=SUBJECTS)

# Тестті бастау
@app.route('/start', methods=['POST'])
def start_test():
    name = request.form.get('name')
    subject = request.form.get('subject')
    access_code = request.form.get('access_code')

    valid_codes = {
        'Информатика': 'inf2024',
        'Қазақстан тарихы': 'tar2024'
    }

    if valid_codes.get(subject) != access_code:
        return render_template('index.html', error="Құпия код дұрыс емес!", subjects=SUBJECTS)

    # Тест сұрақтарын жүктеу
    filename = 'data/questions_informatika.json' if subject == 'Информатика' else 'data/questions_tarikh.json'
    with open(f'./{filename}', 'r', encoding='utf-8') as f:
        questions = json.load(f)

    return render_template('test.html', name=name, subject=subject, questions=questions)

# Тест нәтижесін қабылдау
@app.route('/submit', methods=['POST'])
@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    name = data['name']
    subject = data['subject']
    score = data['score']

    result = {
        'name': name,
        'subject': subject,
        'score': score
    }

    # Нәтижелерді сақтаймыз
    results_file = 'results.json'
    if os.path.exists(results_file):
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = []

    results.append(result)

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ✅ Telegram хабарлама жіберу
    TOKEN = '8081473807:AAHwArxl0zuBAtrLe6Rq4HZrds4FftOzFW0'
    CHAT_ID = '916119312'

    message = f"📥 Жаңа тест нәтижесі:\n👤 {name}\n📚 {subject}\n📊 Ұпай: {score}"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram хабарлама жіберілмеді:", e)

    return jsonify({'redirect': '/result?name=' + name + '&subject=' + subject + '&score=' + str(score)})

# Нәтиже беті
@app.route('/result')
def result():
    name = request.args.get('name')
    subject = request.args.get('subject')
    score = request.args.get('score')
    return render_template('result.html', name=name, subject=subject, score=score)

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        subject = request.form.get('subject')
        password = request.form.get('password')

        correct_passwords = {
            'Информатика': '12348',
            'Қазақстан тарихы': '12349'
        }

        if correct_passwords.get(subject) == password:
            session['teacher_logged_in'] = True
            session['teacher_subject'] = subject
            return redirect('/teacher/panel')
        else:
            return render_template('teacher_login.html', error='Құпия сөз дұрыс емес!')

    return render_template('teacher_login.html')

# 🧑‍🏫 Мұғалім панелі
@app.route('/teacher/panel')
def teacher_panel():
    if not session.get('teacher_logged_in'):
        return redirect('/teacher/login')

    teacher_subject = session.get('teacher_subject')
    results = []

    if os.path.exists('results.json'):
        with open('results.json', 'r', encoding='utf-8') as f:
            all_results = json.load(f)
            results = [r for r in all_results if r['subject'] == teacher_subject]

    test_files = os.listdir('uploaded_tests') if os.path.exists('uploaded_tests') else []

    return render_template('teacher_panel.html', results=results, test_files=test_files)

# Серверді іске қосу
@app.route('/teacher/add_test', methods=['GET', 'POST'])

def add_test():
    if not session.get('teacher_logged_in'):
        return redirect('/teacher/login')

    if request.method == 'POST':
        subject = request.form.get('subject')
        questions = []
        index = 0

        while True:
            q_text = request.form.get(f'question_{index}')
            q_answer = request.form.get(f'correct_{index}')
            if not q_text or q_answer is None:
                break

            # 📥 Сұрақ суретін жүктеу
            image_file = request.files.get(f'image_{index}')
            image_path = None
            if image_file and image_file.filename != '':
                ext = image_file.filename.split('.')[-1]
                image_name = f"q_{uuid.uuid4().hex}.{ext}"
                image_path = f"static/images/{image_name}"
                image_file.save(image_path)

            options = []
            opt_idx = 0
            while True:
                opt_text = request.form.get(f'option_{index}_{opt_idx}')
                opt_image = request.files.get(f'option_img_{index}_{opt_idx}')
                if not opt_text:
                    break

                opt_image_url = None
                if opt_image and opt_image.filename != '':
                    ext = opt_image.filename.split('.')[-1]
                    image_name = f"opt_{uuid.uuid4().hex}.{ext}"
                    opt_image_url = f"static/images/{image_name}"
                    opt_image.save(opt_image_url)

                options.append({
                    'text': opt_text.strip(),
                    'image': opt_image_url  # None болуы мүмкін
                })
                opt_idx += 1

            questions.append({
                'question': q_text.strip(),
                'image': image_path,  # None болуы мүмкін
                'options': options,
                'answer': int(q_answer)
            })

            index += 1

         # Тағайындалған JSON файл
        subject_file = 'data/questions_informatika.json' if subject == 'Информатика' else 'data/questions_tarikh.json'

        # Егер файл бұрыннан бар болса — сұрақтар тізіміне қосамыз
        if os.path.exists(subject_file):
            with open(subject_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if 'single' in existing_data:
                    existing_data['single'].extend(questions)
                else:
                    existing_data['single'] = questions
        else:
            existing_data = {'single': questions}

        # Жаңа сұрақтармен бірге қайта жазу
        with open(subject_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)


        return redirect('/teacher/panel')

    return render_template('add_test.html')

if __name__ == '__main__':
    app.run(debug=True)

