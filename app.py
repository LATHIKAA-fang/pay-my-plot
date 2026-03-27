from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.security import check_password_hash
import mysql.connector
from datetime import datetime
import io
import csv
import qrcode

app = Flask(__name__)
app.secret_key = "secret"
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('buyer_login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('buyer_dashboard.html')

# ---------------- MySQL ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="saranmanjulxlt4444",
    database="real_estate"
)

cursor = db.cursor(dictionary=True)

OWNER_UPI = "lathikaasree1@okaxis"


# ---------------- Home ----------------
@app.route('/')
def index():
    return render_template("index.html")


# ---------------- Buyer Login ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM buyer WHERE email=%s",(email,))
        buyer = cursor.fetchone()

        if buyer and check_password_hash(buyer['password'],password):

            session['buyer_id'] = buyer['buyer_id']
            return redirect('/dashboard')

        return "Invalid Login"

    return render_template("buyer_login.html")


# ---------------- Buyer Dashboard ----------------
@app.route('/dashboard')
def dashboard():

    if 'buyer_id' not in session:
        return redirect('/login')

    buyer_id = session['buyer_id']

    cursor.execute("SELECT * FROM buyer WHERE buyer_id=%s",(buyer_id,))
    buyer = cursor.fetchone()

    cursor.execute("SELECT * FROM payment WHERE buyer_id=%s",(buyer_id,))
    payments = cursor.fetchall()

    return render_template(
        "buyer_dashboard.html",
        buyer=buyer,
        payments=payments,
        upi=OWNER_UPI
    )


# ---------------- Generate Payment ----------------
@app.route('/pay')
def pay():

    if 'buyer_id' not in session:
        return redirect('/login')

    buyer_id = session['buyer_id']

    cursor.execute("SELECT due_amount FROM buyer WHERE buyer_id=%s",(buyer_id,))
    buyer = cursor.fetchone()

    amount = buyer['due_amount']   # always monthly due

    return redirect(f"/payment_page/{amount}")


# ---------------- Payment Page ----------------
@app.route('/payment_page/<amount>')
def payment_page(amount):

    upi_link = f"upi://pay?pa={OWNER_UPI}&pn=Lathikaa&am={amount}&cu=INR"

    return render_template(
        "payment_page.html",
        amount=amount,
        upi=OWNER_UPI,
        upi_link=upi_link
    )



# ---------------- Owner Dashboard ----------------
@app.route('/owner_dashboard')
def owner_dashboard():

    cursor.execute("""
        SELECT p.payment_id, p.buyer_id, p.amount, p.payment_date, p.status, b.name
        FROM pending_payment p
        JOIN buyer b ON p.buyer_id = b.buyer_id
        WHERE p.status='Pending'
    """)

    pending = cursor.fetchall()

    return render_template('owner_dashboard.html', pending=pending)


# ---------------- Confirm Payment ----------------
@app.route('/confirm_payment/<int:id>',methods=['POST'])
def confirm_payment(id):

    cursor.execute("SELECT * FROM pending_payment WHERE payment_id=%s",(id,))
    row = cursor.fetchone()

    buyer_id = row['buyer_id']
    amount = row['amount']

    cursor.execute("UPDATE pending_payment SET status='Confirmed' WHERE payment_id=%s",(id,))

    cursor.execute("""
    INSERT INTO payment
    (buyer_id,amount_paid,payment_date,payment_mode)
    VALUES (%s,%s,CURDATE(),'UPI')
    """,(buyer_id,amount))

    cursor.execute("""
    UPDATE buyer
    SET balance_amount = balance_amount - %s
    WHERE buyer_id=%s
    """,(amount,buyer_id))

    db.commit()

    return redirect('/owner_dashboard')


# ---------------- QR Generator ----------------
@app.route('/generate_qr/<amount>')
def generate_qr(amount):

    upi_link = f"upi://pay?pa={OWNER_UPI}&pn=Lathikaa&am={amount}&cu=INR"

    img = qrcode.make(upi_link)

    buffer = io.BytesIO()
    img.save(buffer,"PNG")
    buffer.seek(0)

    return send_file(buffer,mimetype='image/png')


# ---------------- Receipt ----------------
@app.route('/download/<int:id>')
def receipt(id):

    cursor.execute("SELECT * FROM payment WHERE payment_id=%s",(id,))
    payment = cursor.fetchone()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["PaymentID","Buyer","Amount","Date","Mode"])

    writer.writerow([
        payment['payment_id'],
        payment['buyer_id'],
        payment['amount_paid'],
        payment['payment_date'],
        payment['payment_mode']
    ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="receipt.csv"
    )


# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(debug=True)
