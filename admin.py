from werkzeug.security import generate_password_hash
import mysql.connector
from datetime import datetime

# ---------------- MySQL Connection ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="saranmanjulxlt4444",
    database="real_estate"
)

cursor = db.cursor()

TOTAL_PRICE = 400000
MONTHLY_DUE = 6000


# ---------------- Add Sample Buyers ----------------
def add_sample_buyers():

    buyers = [
        ("Alice","1990-05-15","alice@example.com","alice123","Block A Plot 10",10000),
        ("Bob","1985-09-20","bob@example.com","bob123","Block B Plot 5",20000),
        ("Charlie","1992-01-10","charlie@example.com","charlie123","Block C Plot 3",10000)
    ]

    for b in buyers:

        name,dob,email,password,location,advance = b

        hashed_password = generate_password_hash(password)

        balance = TOTAL_PRICE - advance

        months = balance // MONTHLY_DUE

        due_end_year = datetime.now().year + (months // 12)

        cursor.execute("SELECT * FROM buyer WHERE email=%s",(email,))
        exists = cursor.fetchone()

        if exists:
            print(email,"already exists")
            continue

        cursor.execute("""
        INSERT INTO buyer
        (name,dob,email,password,land_location,total_amount,initial_paid,balance_amount,due_amount,due_end_year)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            name,
            dob,
            email,
            hashed_password,
            location,
            TOTAL_PRICE,
            advance,
            balance,
            MONTHLY_DUE,
            due_end_year
        )
        )

        print(name,"months to complete:",months)

    db.commit()
    print("Buyers added successfully")


# ---------------- Add Sample Payments ----------------
def add_sample_payments():

    cursor.execute("SELECT buyer_id FROM buyer")
    buyers = cursor.fetchall()

    for (buyer_id,) in buyers:

        amount = 6000

        cursor.execute("""
        INSERT INTO payment
        (buyer_id,amount_paid,payment_date,payment_mode)
        VALUES (%s,%s,%s,%s)
        """,
        (buyer_id,amount,datetime.today().date(),"Bank")
        )

    db.commit()
    print("Sample payments added")


# ---------------- Run ----------------
if __name__ == "__main__":

    add_sample_buyers()
    add_sample_payments()

    print("Admin setup completed")
