from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wallet.db'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define ExpenseCategory model
class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Define Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

# User Registration Endpoint
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not (username and email and password):
        return jsonify({'message': 'All fields are required'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'Email already exists'}), 400

    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# User Login Endpoint
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200

# Retrieve all expense categories Endpoint
@app.route('/api/categories', methods=['GET'])
@jwt_required()
def get_categories():
    categories = ExpenseCategory.query.filter_by(user_id=get_jwt_identity()).all()
    return jsonify([category.name for category in categories]), 200

# Add a new expense category Endpoint
@app.route('/api/categories', methods=['POST'])
@jwt_required()
def add_category():
    data = request.json
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Name is required'}), 400

    new_category = ExpenseCategory(name=name, user_id=get_jwt_identity())
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'message': 'Category added successfully'}), 201

# Delete an existing expense category Endpoint
@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    category = ExpenseCategory.query.get(category_id)
    if not category or category.user_id != get_jwt_identity():
        return jsonify({'message': 'Category not found'}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted successfully'}), 200

# Add a new expense Endpoint
@app.route('/api/expenses', methods=['POST'])
@jwt_required()
def add_expense():
    data = request.json
    title = data.get('title')
    date = datetime.strptime(data.get('date'), '%Y-%m-%d')
    amount = float(data.get('amount'))
    category_id = data.get('category_id')

    if not (title and date and amount and category_id):
        return jsonify({'message': 'All fields are required'}), 400

    new_expense = Expense(title=title, date=date, amount=amount, category_id=category_id, user_id=get_jwt_identity())
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({'message': 'Expense added successfully'}), 201

# Retrieve paginated list of user's expenses Endpoint
@app.route('/api/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    user_id = get_jwt_identity()
    expenses = Expense.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page)

    return jsonify({
        'expenses': [{'title': expense.title, 'date': str(expense.date), 'amount': expense.amount} for expense in expenses.items],
        'total_pages': expenses.pages,
        'current_page': expenses.page
    }), 200

# Group user expenses by category Endpoint
@app.route('/api/expenses/grouped', methods=['GET'])
@jwt_required()
def get_grouped_expenses():
    grouped_expenses = {}
    user_id = get_jwt_identity()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    for expense in expenses:
        if expense.category_id not in grouped_expenses:
            grouped_expenses[expense.category_id] = []
        grouped_expenses[expense.category_id].append({'title': expense.title, 'date': str(expense.date), 'amount': expense.amount})

    return jsonify(grouped_expenses), 200

# Retrieve monthly expense data for a specific category Endpoint
@app.route('/api/expenses/category/<int:category_id>/monthly', methods=['GET'])
@jwt_required()
def get_monthly_expenses(category_id):
    # Implement logic to retrieve monthly expense data for a specific category
    return jsonify({'message': 'This endpoint is under construction'}), 501

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)

