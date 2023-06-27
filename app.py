from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)


# Определение моделей

class Product(db.Model):  # Определение модели Product
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    orders = db.relationship('Order', backref='product', lazy=True)

    def __init__(self, name, price, created_at):
        self.name = name
        self.price = price
        self.created_at = created_at


class Order(db.Model):  # Определение модели Order
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    order_created_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)

    def __init__(self, product_id, order_created_at, status):
        self.product_id = product_id
        self.order_created_at = order_created_at
        self.status = status


class Bill(db.Model):  # Определение модели Bill
    __tablename__ = 'bill'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_created_at = db.Column(db.DateTime, nullable=False)
    bill_created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, order_id):
        order = Order.query.get(order_id)
        product = Product.query.get(order.product_id)

        self.name = product.name
        self.price = product.price
        self.order_created_at = order.order_created_at


# Создание таблиц и добавление продуктов

@app.before_request
def setup():
    # Создаем таблицы в базе данных
    with app.app_context():
        db.create_all()

    # Проверка добавлены ли продукты
    existing_products = Product.query.all()
    if existing_products:
        return

    # Создаем и добавляем продукты
    fan = Product(name='Fan', price=550.0, created_at=datetime.now())
    lamp = Product(name='Lamp', price=25.0, created_at=datetime.now())
    mic = Product(name='Mic', price=100.0, created_at=datetime.now())

    db.session.add(fan)
    db.session.add(lamp)
    db.session.add(mic)
    db.session.commit()


# Маршруты

@app.route('/products', methods=['GET'])  # Маршрут для получения списка продуктов
def get_products():
    products = Product.query.all()
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'created_at': product.created_at
        })
    return jsonify(result)


@app.route('/orders', methods=['GET'])  # Маршрут для получения списка заказов
def get_orders():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date and end_date:
        # Фильтрация по дате
        orders = Order.query.filter(Order.order_created_at >= start_date, Order.order_created_at <= end_date).all()
    else:
        # Получение всего списка заказов
        orders = Order.query.all()

    result = []
    for order in orders:
        product = Product.query.get(order.product_id)
        result.append({
            'id': order.id,
            'product_id': order.product_id,
            'order_created_at': order.order_created_at,
            'status': order.status,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'created_at': product.created_at
            }
        })
    return jsonify(result)


@app.route('/bills', methods=['GET'])  # Маршрут для получения списка счетов
def get_bills():
    bills = Bill.query.all()
    result = []
    for bill in bills:
        result.append({
            'id': bill.id,
            'name': bill.name,
            'price': bill.price,
            'order_created_at': bill.order_created_at,
            'bill_created_at': bill.bill_created_at
        })
    return jsonify(result)


@app.route('/add_order', methods=['PUT'])  # Маршрут для добавления заказа
def add_order():
    data = request.get_json()
    product_id = int(data['product_id'])
    order_created_at = datetime.now()
    status = "received"

    product = Product.query.filter_by(id=product_id).first()

    if not product:
        abort(404, 'Product not found.')

    new_order = Order(product_id=product_id, order_created_at=order_created_at, status=status)
    db.session.add(new_order)
    db.session.commit()

    return 'Order added successfully!'


@app.route('/orders/<int:order_id>', methods=['PUT'])  # Маршрут для изменения статуса заказа по его идентификатору
def update_order(order_id):
    data = request.get_json()
    new_status = data.get('status')

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    order.status = new_status
    db.session.commit()

    return jsonify({'message': 'Order status updated successfully'})


@app.route('/add_bill', methods=['POST'])  # Маршрут для добавления счета
def create_bill():
    data = request.get_json()
    order_id = data['order_id']

    new_bill = Bill(order_id=order_id)
    db.session.add(new_bill)
    db.session.commit()

    return 'Bill created successfully!'


if __name__ == '__main__':
    app.run()
