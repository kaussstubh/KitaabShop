from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import random
import smtplib  # To send email
from flask import session

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')


def getLoginDetails():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = ?", (session['email'],))
            userId, firstName = cur.fetchone()

            # Fetch the count of items in the cart
            cur.execute("SELECT COUNT(bookId) FROM kart WHERE userId = ?", (userId,))
            noOfItems = cur.fetchone()[0]
    conn.close()
    return loggedIn, firstName, noOfItems

@app.route("/")
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    # Get sorting option from query parameters, default is 'nameAsc'
    sort_option = request.args.get('sort', 'nameAsc')

    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()

        # Apply sorting based on the query parameter
        if sort_option == 'nameAsc':
            cur.execute('SELECT * FROM books ORDER BY title ASC')
        elif sort_option == 'nameDesc':
            cur.execute('SELECT * FROM books ORDER BY title DESC')
        elif sort_option == 'priceLowHigh':
            cur.execute('SELECT * FROM books ORDER BY price ASC')
        elif sort_option == 'priceHighLow':
            cur.execute('SELECT * FROM books ORDER BY price DESC')
        else:
            cur.execute('SELECT * FROM books')  # Default sorting
        itemData = cur.fetchall()

        cur.execute('SELECT categoryId, categoryName FROM categories')
        categoryData = cur.fetchall()

    return render_template('home.html', itemData=itemData, categoryData=categoryData, sort=sort_option, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/add")
def admin():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT categoryId, categoryName FROM categories")
        categories = cur.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)

@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        categoryId = int(request.form['category'])

        #Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        with sqlite3.connect(DATABASE_PATH) as conn:
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO books (title, price, author, image, stock) VALUES (?, ?, ?, ?, ?)''', (name, price, description, imagename, stock))
                conn.commit()
                msg="added successfully"
            except:
                msg="error occured"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('root'))

@app.route("/remove")
def remove():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT bookId, title, price, description, image, stock FROM books')
        data = cur.fetchall()
    conn.close()
    return render_template('remove.html', data=data)

@app.route("/removeItem")
def removeItem():
    bookId = request.args.get('bookId')
    with sqlite3.connect(DATABASE_PATH) as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM books WHERE bookId = ?', (bookId, ))
            conn.commit()
            msg = "Deleted successsfully"
        except:
            conn.rollback()
            msg = "Error occured"
    conn.close()
    print(msg)
    return redirect(url_for('root'))

@app.route("/displayCategory")
def displayCategory():
        loggedIn, firstName, noOfItems = getLoginDetails()
        categoryId = request.args.get("categoryId")
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT books.bookId, books.title, books.price, books.image, categories.categoryName FROM books, categories WHERE books.categoryId = categories.categoryId AND categories.categoryId = ?", (categoryId, ))
            data = cur.fetchall()
        conn.close()
        categoryName = data[0][4]
        data = parse(data)
        print(data)
        return render_template('displayCategory.html', data=data[0], loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryName=categoryName)

@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = ?", (session['email'], ))
        profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

# Update profile route to handle form submission
@app.route("/updateProfile", methods=["POST"])
def updateProfile():
    if 'email' not in session:
        return redirect(url_for('loginForm'))

    email = session['email']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    address1 = request.form['address1']
    address2 = request.form['address2']
    zipcode = request.form['zipcode']
    city = request.form['city']
    state = request.form['state']
    country = request.form['country']
    phone = request.form['phone']

    # Update user data in the database
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ?
                       WHERE email = ?""",
                    (firstName, lastName, address1, address2, zipcode, city, state, country, phone, email))
        conn.commit()

    return redirect(url_for('viewProfile'))

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPasswordHashed = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        confirmPassword = request.form['cpassword']

        # Basic server-side validation
        if newPassword != confirmPassword:
            return render_template("changePassword.html", msg="New password and confirm password do not match")

        newPasswordHashed = hashlib.md5(newPassword.encode()).hexdigest()

        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = ?", (session['email'], ))
            userId, password = cur.fetchone()

            if password == oldPasswordHashed:
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPasswordHashed, userId))
                    conn.commit()
                    msg = "Password changed successfully!"
                except:
                    conn.rollback()
                    msg = "Error: Password change failed."
            else:
                msg = "Incorrect old password."
        conn.close()

        return render_template("changePassword.html", msg=msg,loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
    else:
        return render_template("changePassword.html",loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/loginForm")
def loginForm():
    # Check if user is already logged in
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')


@app.route('/login', methods=['POST'])
def login():
    # Mock login credentials check (replace with DB checks as needed)
    email = request.form['email']
    password = request.form['password']

    # Example credentials to match with
    if email == "testuser@example.com" and password == "Test@1234":
        # Generate a mock OTP (for demonstration purposes)
        otp = '123456'
        session['otp'] = otp  # Store OTP in session temporarily
        session['temp_email'] = email  # Store email temporarily (not logged in yet)

        # Redirect to OTP verification page
        return redirect(url_for('otp_screen'))
    else:
        # Invalid credentials case
        return render_template('login.html', error="Invalid email or password.")


@app.route('/otp', methods=['GET', 'POST'])
def otp_screen():
    # Check if the temp_email exists in session (this means user has entered credentials but hasn't verified OTP)
    if 'temp_email' not in session:
        return redirect(url_for('loginForm'))  # If not logged in, redirect to login
    
    if request.method == 'POST':
        entered_otp = request.form['otp']

        # Check if entered OTP matches the session OTP
        if entered_otp == session.get('otp'):
            # OTP is correct, login the user now by storing email in session
            session['email'] = session['temp_email']
            session.pop('otp', None)  # Remove OTP from session
            session.pop('temp_email', None)  # Remove temporary email

            return render_template('otp_success.html', email=session['email'])
        else:
            # Invalid OTP, reload the OTP page with an error
            return render_template('otp.html', error="Invalid OTP, try again.")
    
    return render_template('otp.html')

@app.route('/logout')
def logout():
    session.pop('email', None)  # Clear the session (logout)
    session.pop('otp', None)
    session.pop('temp_email', None)  # Clear temp email if any
    return redirect(url_for('loginForm'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/send-reset-link', methods=['POST'])
def send_reset_link():
    email = request.form.get('email')
    
    # In a real application, you would verify the email and send an actual reset link here.
    # For now, we will simulate the process.
    if email:
        # Simulate sending a password reset link (mock)
        # You could show the message that "a password reset link has been sent"
        return render_template('send_reset_link.html', email=email)
    else:
        # If email is empty, you can reload the form with an error message
        return render_template('forgot_password.html', error="Please enter a valid email.")


@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    bookId = request.args.get('bookId')
    if not bookId or not bookId.isdigit():
        # Handle case where bookId is not valid (e.g., redirect to an error page)
        return redirect(url_for('root', msg="Invalid book ID"))
    bookId = int(bookId)
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT bookId, title, price, description, image, stock FROM books WHERE bookId = ?', (bookId, ))
        productData = cur.fetchone()
    conn.close()
    return render_template("productDescription.html", data=productData, loggedIn = loggedIn, firstName = firstName, noOfItems = noOfItems)

@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        bookId = int(request.args.get('bookId'))
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'],))
            userId = cur.fetchone()[0]
            
            try:
                # Insert the selected book into the cart
                cur.execute("INSERT INTO kart (userId, bookId) VALUES (?, ?)", (userId, bookId))
                conn.commit()
                msg = "Added to cart successfully"
            except:
                conn.rollback()
                msg = "Error occurred while adding to cart"
        conn.close()
        # Redirect back to the home page, or wherever appropriate
        return redirect(url_for('cart'))

@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]
        cur.execute("SELECT books.bookId, books.title, books.price, books.image FROM books, kart WHERE books.bookId = kart.bookId AND kart.userId = ?", (userId, ))
        books = cur.fetchall()
    totalPrice = 0
    for row in books:
        totalPrice += row[2]
    return render_template("cart.html", books = books, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    bookId = int(request.args.get('bookId'))
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM kart WHERE userId = ? AND bookId = ?", (userId, bookId))
            conn.commit()
            msg = "removed successfully"
        except:
            conn.rollback()
            msg = "error occured"
    conn.close()
    return redirect(url_for('root'))


def is_valid(email, password):
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Parse form data    
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']

        try:
            # Check if email already exists
            with sqlite3.connect(DATABASE_PATH) as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM users WHERE email = ?", (email,))
                existing_user = cur.fetchone()

                if existing_user:
                    # Return an error message if email already exists
                    return render_template("register.html", error="Email already registered. Please try logging in.")

                # Hash the password
                hashed_password = hashlib.md5(password.encode()).hexdigest()

                # Insert new user into the database
                cur.execute('INSERT INTO users (username, password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                            (username, hashed_password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone))
                con.commit()

                # On successful registration, redirect to login with success message
                return render_template("login.html", error="Registered successfully. Please login.")
        except Exception as e:
            print(f"Error occurred during registration: {e}")
            return render_template("register.html", error="An error occurred during registration. Please try again.")
    return render_template("register.html")

@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans
@app.route("/checkout")
def checkout():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
        userId = cur.fetchone()[0]
        cur.execute("SELECT books.bookId, books.title, books.price FROM books, kart WHERE books.bookId = kart.bookId AND kart.userId = ?", (userId,))
        books = cur.fetchall()
    
    totalPrice = sum([row[2] for row in books])
    
    return render_template("checkout.html", books=books, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/confirmCheckout", methods=["POST"])
def confirmCheckout():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    
    email = session['email']
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        
        # Get the userId from the session
        cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
        userId = cur.fetchone()[0]
        
        # Get the books in the cart
        cur.execute("SELECT books.bookId, books.price FROM books, kart WHERE books.bookId = kart.bookId AND kart.userId = ?", (userId,))
        cartItems = cur.fetchall()
        
        if not cartItems:
            return redirect(url_for('cart', msg="Your cart is empty."))
        
        # Calculate total price
        totalPrice = sum([item[1] for item in cartItems])
        
        # Create a new order
        cur.execute("INSERT INTO orders (userId, total, date) VALUES (?, ?, datetime('now'))", (userId, totalPrice))
        orderId = cur.lastrowid  # Get the ID of the newly created order
        
        # Add items from the cart to the order_items table
        for item in cartItems:
            cur.execute("INSERT INTO order_items (orderId, bookId, quantity) VALUES (?, ?, ?)", (orderId, item[0], 1))  # Assuming quantity = 1
        
        # Clear the cart
        cur.execute("DELETE FROM kart WHERE userId = ?", (userId,))
        
        conn.commit()
    
    return redirect(url_for('orders'))  # Redirect to orders page after successful checkout


@app.route("/account/orders")
def orders():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
        userId = cur.fetchone()[0]
        
        # Get the user's orders
        cur.execute("SELECT orderId, date, total FROM orders WHERE userId = ?", (userId,))
        orders = cur.fetchall()
    
    return render_template("orders.html", orders=orders,loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/payment")
def payment():
    if 'email' not in session:
        return redirect(url_for('loginForm'))

    loggedIn, firstName, noOfItems = getLoginDetails()
    
    # Fetch total price from the checkout flow or session
    totalPrice = session.get('totalPrice', 0)

    return render_template("payment.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, totalPrice=totalPrice)

@app.route("/processPayment", methods=["POST"])
def processPayment():
    if 'email' not in session:
        return redirect(url_for('loginForm'))

    # Mock validation of payment details
    cardNumber = request.form.get("cardNumber")
    expiryDate = request.form.get("expiryDate")
    cvv = request.form.get("cvv")
    nameOnCard = request.form.get("nameOnCard")

    # Add some basic mock validation
    if len(cardNumber) == 16 and len(cvv) == 3:
        # Retrieve userId
        email = session['email']
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
            userId = cur.fetchone()[0]

            # Get the books in the cart
            cur.execute("SELECT books.bookId, books.price FROM books, kart WHERE books.bookId = kart.bookId AND kart.userId = ?", (userId,))
            cartItems = cur.fetchall()

            if not cartItems:
                return redirect(url_for('cart', msg="Your cart is empty."))

            # Calculate total price
            totalPrice = sum([item[1] for item in cartItems])

            try:
                # Insert new order in the orders table
                cur.execute("INSERT INTO orders (userId, total, date) VALUES (?, ?, datetime('now'))", (userId, totalPrice))
                orderId = cur.lastrowid  # Capture the newly created orderId

                # Insert items into the order_items table
                for item in cartItems:
                    cur.execute("INSERT INTO order_items (orderId, bookId, quantity) VALUES (?, ?, ?)", (orderId, item[0], 1))  # Assuming quantity = 1

                # Clear the cart
                cur.execute("DELETE FROM kart WHERE userId = ?", (userId,))
                conn.commit()

                # Redirect to the order confirmation page with the new orderId
                return redirect(url_for('orderConfirmation', orderId=orderId))

            except Exception as e:
                conn.rollback()
                return render_template("payment.html", error="An error occurred while processing your order.")
        conn.close()
    else:
        # Mock failure
        return render_template("payment.html", error="Invalid card details. Please try again.")


@app.route("/orderConfirmation/<int:orderId>")
def orderConfirmation(orderId):
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']

    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        
        # Get userId from session email
        cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
        userId = cur.fetchone()[0]
        
        # Fetch order details for the provided orderId
        cur.execute("SELECT total, date FROM orders WHERE orderId = ? AND userId = ?", (orderId, userId))
        orderData = cur.fetchone()

        if orderData:
            totalPrice, orderDate = orderData
            deliveryDate = "Estimated 3-5 business days"  # You can calculate this or leave it static
        else:
            return redirect(url_for('orders', msg="Order not found."))
    
    return render_template(
        "orderConfirmation.html",
        loggedIn=loggedIn,
        firstName=firstName,
        noOfItems=noOfItems,
        orderId=orderId,
        totalPrice=totalPrice,
        deliveryDate=deliveryDate,
        orderDate=orderDate
    )


@app.route("/account/profile/view")
def viewProfile():
    if 'email' not in session:
        return redirect(url_for('loginForm'))  # If not logged in, redirect to login page
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']

    # Fetch user data from the database
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT firstName, lastName, email, phone, address1, address2, city, state, country, zipcode FROM users WHERE email = ?", (email,))
        user_data = cur.fetchone()

    if user_data:
        # Create a dictionary of user details for easy access in the template
        userData = {
            'firstName': user_data[0],
            'lastName': user_data[1],
            'email': user_data[2],
            'phone': user_data[3],
            'address1': user_data[4],
            'address2': user_data[5],
            'city': user_data[6],
            'state': user_data[7],
            'country': user_data[8],
            'zipcode': user_data[9]
        }

        # Render the view profile page with the user data
        return render_template('viewProfile.html', userData=userData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
    
    else:
        return "User not found", 404  # If the user data is not found


if __name__ == '__main__':
    app.run(debug=True)
