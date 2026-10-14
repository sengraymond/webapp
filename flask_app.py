import os

from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["DEBUG"] = True
environment = "Production"

db_host = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')
db_port = os.environ.get('DB_PORT')
db_username = os.environ.get('DB_USERNAME')
db_password = os.environ.get('DB_PASSWORD')
app.secret_key = os.environ.get('APP_SECRET_KEY')

SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {
        "ssl": {
            "ca": "/webapp/mysql.pem"
        }
    }
}

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    role = db.Column(db.String(128), unique=True, nullable=False)    
    password_hash = db.Column(db.String(256), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)    


@app.route("/", methods=["GET", "POST"])
def comments():
    if request.method == "GET":
        return render_template("main_page.html", environment=environment)

    if not current_user.is_authenticated:
        return redirect(url_for('comments'))

    return redirect(url_for('comments'))


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login_page.html", error=False, environment=environment)

    username = request.form["username"]
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(request.form["password"]):
        return render_template("login_page.html", error=True, environment=environment)

    login_user(user)
    return redirect(url_for('inventory_view'))


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('comments'))


@app.route("/inventory/", methods=["GET", "POST"])
@login_required
def inventory():
    # Only allow "logistics" role to access this page
    if current_user.role != "logistics":
        return redirect(url_for("inventory_view"))

    # Only allow access to this page in Production env
    if environment != "Production":
        return redirect(url_for("inventory_view"))

    error = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            name = request.form.get("name", "").strip()
            quantity_text = request.form.get("quantity", "").strip()
            try:
                quantity = int(quantity_text)
            except ValueError:
                quantity = -1

            if not name or quantity < 0:
                error = "Enter an item name and a quantity of zero or more."
            elif Inventory.query.filter_by(name=name).first():
                error = "An item with that name already exists."
            else:
                db.session.add(Inventory(name=name, quantity=quantity))
                db.session.commit()
                return redirect(url_for("inventory"))

        elif action == "update":
            item = Inventory.query.get(request.form.get("item_id"))
            quantity_text = request.form.get("quantity", "").strip()
            try:
                quantity = int(quantity_text)
            except ValueError:
                quantity = -1

            if item and quantity >= 0:
                item.quantity = quantity
                db.session.commit()
                return redirect(url_for("inventory"))
            error = "Quantity must be a whole number of zero or more."

        elif action == "delete":
            item = Inventory.query.get(request.form.get("item_id"))
            if item:
                db.session.delete(item)
                db.session.commit()
                return redirect(url_for("inventory"))

    items = Inventory.query.order_by(Inventory.name.asc()).all()
    return render_template("inventory_page.html", items=items, error=error)


@app.route("/view/", methods=["GET"])
@login_required
def inventory_view():
    items = Inventory.query.order_by(Inventory.name.asc()).all()
    return render_template("inventory_readonly_page.html", items=items)

