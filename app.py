

from flask import Flask, render_template, request, session, redirect, url_for, current_app
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired
import random
import sqlite3

import secrets
import string

def create_app():
    app = Flask(__name__)
    app.secret_key = "your_secret_key"  # Change this to a secure secret key
    app.config['DATABASE'] = "conjoint_data.db"
    
    with app.app_context():
        create_database()

    return app

# Attribute levels
attributes = {
    "decision": ["suggest_diagnosis", "provide_information"],
    "severity": ["less_severe", "moderate_severe", "severe_only"],
    "explanation": ["clearly_explained", "not_explained_well"],
    "performance": ["accuracy_equal", "accuracy_comparable", "accuracy_better"],
    "responsibility": ["hospital_responsible", "doctors_responsible", "ai_company_responsible"],
    "discrimination": ["tested_for_discrimination", "not_tested_for_discrimination"],
    "cost": ["lower_cost", "same_cost", "higher_cost"]
}

attributes_labels = {
    "How is AI used for decision-making": ["It is used to suggest diagnosis", "It is used to provide information about the condition"],
    "In what severity is the AI tool used": ["Less severe cases", "Moderate severity Cases", "Severe Cases only"],
    "Is the explanation provided by the AI tool": ["Yes, clear explanation of decision is provided", "No, only the decision is provided"],
    "How is the accuracy compared to a doctor?": ["The accuracy is equal", "The accuracy is comparable", "The accuracy of the AI tool is better"],
    "Who is responsible if the AI tool makes a mistake?": ["The hospital is responsible", "The doctors are responsible", "The AI company is responsible"],
    "Has the dataset been tested so that it does not discriminate by race and gender?": ["Robust testing has been performed", "Testing for discriminated not performed"],
    "How does it affect the cost for the patient where the AI tool is used?": ["The cost is lower", "The cost is not different", "The cost is higher"]
}

class SurveyForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    race_ethnicity = SelectField('Race/Ethnicity', choices=[
        ('non_hispanic_white', 'Non-Hispanic White'),
        ('hispanic_white', 'Hispanic White'),
        ('black', 'Black'),
        ('aapi', 'AAPI'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField('Start Conjoint Analysis')

def create_database():
    with current_app.app_context():
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age INTEGER,
                gender TEXT,
                race_ethnicity TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS choices (
                participant_id INTEGER,
                choice_id TEXT,
                decision_a TEXT,
                severity_a TEXT,
                explanation_a TEXT,
                performance_a TEXT,
                responsibility_a TEXT,
                discrimination_a TEXT,
                cost_a TEXT,
                decision_b TEXT,
                severity_b TEXT,
                explanation_b TEXT,
                performance_b TEXT,
                responsibility_b TEXT,
                discrimination_b TEXT,
                cost_b TEXT,
                user_choice TEXT,
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            )
        ''')

        conn.commit()
        conn.close()

def save_participant_info(data):
    with current_app.app_context():
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO participants (age, gender, race_ethnicity) VALUES (?, ?, ?)
        ''', (
            data['age'],
            data['gender'],
            data['race_ethnicity']
        ))

        participant_id = cursor.lastrowid

        conn.commit()
        conn.close()

        # Store participant_id in the session
        session['participant_id'] = participant_id

def save_to_database(participant_id, choice_id, data, user_choice):
    with current_app.app_context():
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()

    cursor.execute('''
            INSERT INTO choices (
                participant_id, choice_id,
                decision_a, severity_a, explanation_a, performance_a, responsibility_a, discrimination_a, cost_a,
                decision_b, severity_b, explanation_b, performance_b, responsibility_b, discrimination_b, cost_b,
                user_choice
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            participant_id,
            choice_id,
            data['hospital_a']['decision'],
            data['hospital_a']['severity'],
            data['hospital_a']['explanation'],
            data['hospital_a']['performance'],
            data['hospital_a']['responsibility'],
            data['hospital_a']['discrimination'],
            data['hospital_a']['cost'],
            data['hospital_b']['decision'],
            data['hospital_b']['severity'],
            data['hospital_b']['explanation'],
            data['hospital_b']['performance'],
            data['hospital_b']['responsibility'],
            data['hospital_b']['discrimination'],
            data['hospital_b']['cost'],
            user_choice
        ))

    conn.commit()
    conn.close()

app = create_app()

def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string

@app.route('/')
def index():
    form = SurveyForm()
    return render_template('landing_page.html', form=form)

@app.route('/conjoint', methods=['POST', 'GET'])
def conjoint():
    choices = generate_choice() 
    ch_id = None

    if request.method == 'POST':
        form = SurveyForm(request.form)
        if form.validate_on_submit():
            # Save participant information
            save_participant_info(request.form.to_dict())
            session['current_choice'] = 1
            choices = generate_choice()
            return render_template('conjoint.html', choices=choices)

    user_choice = request.args.get('choice')
    if user_choice is not None:
        if ch_id is None:
            ch_id = generate_random_string()
            save_to_database(session['participant_id'], ch_id, choices, user_choice)
            
        if session['current_choice'] < 10:
            session['current_choice'] += 1
            choices = generate_choice()
            return render_template('conjoint.html', choices=choices)
        else:
            return redirect(url_for('thankyou'))

    return redirect(url_for('index'))

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

# def generate_choice():
#     hospital_a = {attribute: random.choice(levels) for attribute, levels in attributes.items()}
#     hospital_b = {attribute: random.choice(levels) for attribute, levels in attributes.items()}
#     return {"hospital_a": hospital_a, "hospital_b": hospital_b}

def generate_choice():
    hospital_a = {attribute: random.choice(attributes[attribute]) for attribute in attributes}
    hospital_b = {attribute: random.choice(attributes[attribute]) for attribute in attributes}
    return {"hospital_a": hospital_a, "hospital_b": hospital_b}

if __name__ == '__main__':
    app.run(debug=True)

