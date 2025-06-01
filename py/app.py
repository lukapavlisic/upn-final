from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from tinydb import TinyDB, Query
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Inicializacija TinyDB
db = TinyDB('data.json')
users_table = db.table('users')
cars_table = db.table('cars')
comments_table = db.table('comments')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    budget = request.form.get('budget')
    car_type = request.form.get('type')
    fuel = request.form.get('fuel')
    market = request.form.get('market')
    age = request.form.get('age')
    
    # Custom budget handling
    if budget == 'custom':
        try:
            budget = int(request.form.get('custom_budget', 0))
        except:
            budget = 0
    else:
        budget = int(budget) if budget != 'any' else 999999
    
    # Filtriranje avtomobilov
    cars = cars_table.all()
    filtered_cars = []
    
    for car in cars:
        if car['price'] <= budget:
            if car_type == 'any' or car['type'] == car_type:
                if fuel == 'any' or car['fuel'] == fuel:
                    if market == 'any' or car['market'] == market:
                        if age == 'any' or car['age'] == age:
                            filtered_cars.append(car)
    
    return render_template('results.html', cars=filtered_cars)

@app.route('/car/<int:car_id>')
def car_detail(car_id):
    Car = Query()
    car = cars_table.search(Car.id == car_id)
    if not car:
        return redirect(url_for('index'))
    
    car = car[0]
    comments = comments_table.search(Query().car_id == car_id)
    
    # Izračun povprečne ocene
    if comments:
        avg_rating = sum(c['rating'] for c in comments) / len(comments)
        avg_rating = round(avg_rating, 1)
    else:
        avg_rating = 0
    
    return render_template('car_detail.html', car=car, comments=comments, avg_rating=avg_rating)

@app.route('/vsi-avti')
def vsi_avti():
    cars = cars_table.all()
    return render_template('cars_partial.html', cars=cars)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin_key = request.form.get('admin_key', '')
        
        User = Query()
        if users_table.search(User.username == username):
            flash('Uporabniško ime že obstaja!')
            return render_template('register.html')
        
        is_admin = admin_key == 'Mila'
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        users_table.insert({
            'username': username,
            'password': hashed_password,
            'is_admin': is_admin
        })
        
        flash('Registracija uspešna!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        User = Query()
        user = users_table.search((User.username == username) & (User.password == hashed_password))
        
        if user:
            session['user_id'] = username
            session['is_admin'] = user[0]['is_admin']
            return redirect(url_for('index'))
        else:
            flash('Napačno uporabniško ime ali geslo!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add_comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        return jsonify({'error': 'Morate biti prijavljeni!'}), 401
    
    car_id = int(request.json['car_id'])
    rating = int(request.json['rating'])
    comment_text = request.json['comment']
    
    comment = {
        'car_id': car_id,
        'user': session['user_id'],
        'rating': rating,
        'comment': comment_text,
        'timestamp': datetime.now().isoformat()
    }
    
    comment_id = comments_table.insert(comment)
    comment['id'] = comment_id
    
    return jsonify(comment)

@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Nemate pravic!'}), 403
    
    comment_id = int(request.json['comment_id'])
    comments_table.remove(doc_ids=[comment_id])
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)