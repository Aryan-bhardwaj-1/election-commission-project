
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
print("DB_USER =", os.getenv("DB_USER"))
print("DB_PASSWORD =", os.getenv("DB_PASSWORD"))
print("DB_NAME =", os.getenv("DB_NAME"))
import random
app = Flask(__name__)
app.secret_key = app.secret_key = os.getenv("SECRET_KEY")
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

password = quote_plus(os.getenv("DB_PASSWORD"))

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{password}@localhost/{os.getenv('DB_NAME')}"
)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    aadhaar = db.Column(db.String(20))
    voter_id = db.Column(db.String(50))
    password = db.Column(db.String(255))
    status = db.Column(db.String(20), default="Pending")
    has_voted = db.Column(db.Boolean, default=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    party = db.Column(db.String(100))
    votes = db.Column(db.Integer, default=0)

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)

with app.app_context():
 db.create_all()

 if Candidate.query.count() == 0:

        c1 = Candidate(
            name="bhartiya janta party",
            party="Party A"
        )

        c2 = Candidate(
            name="congress",
            party="Party B"
        )

        c3 = Candidate(
            name="others",
            party="Party C"
        )

        db.session.add(c1)
        db.session.add(c2)
        db.session.add(c3)

        db.session.commit()
@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():

    voter_id = "VOTER" + str(random.randint(1000,9999))
    password = "EC" + str(random.randint(1000,9999))

    voter = Voter(
        name=request.form['name'],
        phone=request.form['phone'],
        email=request.form['email'],
        aadhaar=request.form['aadhaar'],
        voter_id=voter_id,
        password=password
    )

    db.session.add(voter)
    db.session.commit()
    msg = Message(
    'Election Commission Registration',
    sender='bhardwajaryan20060506@gmail.com',
    recipients=[request.form['email']]
)

    msg.body = f"""
Registration Successful

Voter ID: {voter_id}
Password: {password}
"""

    mail.send(msg)
    return f"""
    Registration Successful <br>
    Voter ID: {voter_id} <br>
    Password: {password}
    """
@app.route('/admin')
def admin():
    return render_template('admin_login.html')
@app.route('/admin-login', methods=['POST'])
def admin_login():

    username = request.form['username']
    password = request.form['password']

    if username == "admin" and password == "admin123":
        return redirect('/dashboard')

    return "Invalid Login"
@app.route('/dashboard')
def dashboard():

    voters = Voter.query.all()

    return render_template(
        'dashboard.html',
        voters=voters
    )
@app.route('/approve/<int:id>')
def approve(id):

    voter = db.session.get(Voter, id)

    voter.status = "Approved"

    db.session.commit()

    return redirect('/dashboard')

@app.route('/reject/<int:id>')
def reject(id):

    voter = Voter.query.get(id)

    voter.status = "Rejected"

    db.session.commit()

    return redirect('/dashboard')
@app.route('/voter_login', methods=['GET', 'POST'])
def voter_login():

    if request.method == 'POST':

        voter_id = request.form['voter_id']
        password = request.form['password']

        voter = Voter.query.filter_by(
            voter_id=voter_id,
            password=password
        ).first()

        if voter:

            if voter.status != "Approved":
                return "Your registration is not approved yet."

            session['voter_id'] = voter.id
            print("Session Created:",session['voter_id'])
            
            return redirect('/vote')

        return "Invalid Voter ID or Password"

    return render_template('voter_login.html')

@app.route('/vote')
def vote():

    if 'voter_id' not in session:
        return redirect('/voter_login')

    voter = db.session.get(
        Voter,
        session['voter_id']
    )

    if voter.has_voted:
        return redirect('/results')

    candidates = Candidate.query.all()

    return render_template(
        'vote.html',
        candidates=candidates
    )

@app.route('/candidates')
def candidateas():

    data = Candidate.query.all()

    result = ""

    for c in data:
        result += f"{c.name} - {c.party}<br>"

    return result
@app.route('/submit-vote', methods=['POST'])
def submit_vote():

    if 'voter_id' not in session:
        return redirect('/voter_login')

    voter = db.session.get(
        Voter,
        session['voter_id']
    )

    if voter.has_voted:
        return "You have already voted."

    candidate_id = request.form['candidate']

    candidate = db.session.get(
        Candidate,
        int(candidate_id)
    )

    candidate.votes += 1
    voter.has_voted = True

    db.session.commit()

    return redirect('/results')
@app.route('/results')
def results():

    candidates = Candidate.query.all()

    winner = max(candidates, key=lambda x: x.votes)

    return render_template(
        'results.html',
        candidates=candidates,
        winner=winner
    )
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/voter_login')
    
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
    
    
    