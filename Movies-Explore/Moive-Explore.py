import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import requests
from PIL import Image, ImageTk
from io import BytesIO
import mysql.connector  # Import MySQL Connector
import bcrypt  # For password hashing
import urllib.parse  # Import urllib for URL encoding

# Global variable to track if a user is logged in
is_logged_in = False
current_user_id = None  
selected_seats = []
selected_movie = None
selected_time_slot = None
time_slot_buttons = []
movies_by_genre = {}
weekly_schedule = {}
time_slots = []
seat_buttons = []
movie_posters = {}

def init_db():
    """Initialize the MySQL database."""
    conn = mysql.connector.connect(
        host='localhost',  
        user='root',  
        password='',  
        database='Movies-Explore'  
    )
    return conn

def register_user(email, password, confirm_password):
    """Register a new user."""
    global is_logged_in, current_user_id
    if password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match.")
        return

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (email, password)
            VALUES (%s, %s)
        ''', (email, hashed_password))
        conn.commit()
        current_user_id = cursor.lastrowid  # Get the last inserted user_id
        messagebox.showinfo("Registration Successful", "You have registered successfully!")
        is_logged_in = True  # Set the login status to True after registration
        update_login_register_buttons()  # Update buttons after registration
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error: {err}")
    finally:
        conn.close()

def login_user(email, password):
    """Log in the user."""
    global is_logged_in, current_user_id
    conn = init_db()
    cursor = conn.cursor()
    
    # Check for admin credentials
    if (email == "admin@gmail.com" and password == "admin"):
        create_admin_panel()
        return
    # Check for regular user credentials
    cursor.execute('''
        SELECT user_id, password FROM users WHERE email = %s
    ''', (email,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        hashed_password = result[1].encode('utf-8')  
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            messagebox.showinfo("Login Successful", "Welcome back!")
            is_logged_in = True  # Set the login status
            current_user_id = result[0]  # Store user ID
            update_login_register_buttons()  # Update buttons after login
            return current_user_id  # Return user ID
        else:
            messagebox.showerror("Login Failed", "Invalid email or password.")
    else:
        messagebox.showerror("Login Failed", "Invalid email or password.")
    return None  # Login failed

def update_login_register_buttons():
    """Update the login and register buttons based on login status."""
    if is_logged_in:
        login_button.grid_forget()  # Hide login button
        register_button.grid_forget()  # Hide register button
        logout_button.grid(row=0, column=7, pady=(0, 0), sticky='w')  # Show logout button in the same position as register
    else:
        logout_button.grid_forget()  # Hide logout button
        login_button.grid(row=0, column=6, pady=(0, 0), sticky='e')  # Show login button
        register_button.grid(row=0, column=7, pady=(0, 0), sticky='w')  # Show register button

def logout_user():
    """Log out the user."""
    global is_logged_in, current_user_id
    is_logged_in = False
    current_user_id = None
    update_login_register_buttons() 
    
def create_login_form():
    """Create a login form."""
    login_window = tk.Toplevel()
    login_window.title("Login")
    login_window.configure(bg='#101010')
    login_window.geometry("400x300")  # Set a fixed size for the login window

    tk.Label(login_window, text="Email", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    email_entry = tk.Entry(login_window, width=30, font="Helvetica 12")
    email_entry.pack(pady=5)

    tk.Label(login_window, text="Password", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    password_entry = tk.Entry(login_window, show='*', width=30, font="Helvetica 12")
    password_entry.pack(pady=5)

    tk.Button(login_window, text="Login", command=lambda: login_user(email_entry.get(), password_entry.get()), bg='#ff3b3b', fg='white', font="Helvetica 14 bold", width=15).pack(pady=20)

def create_registration_form():
    """Create a registration form."""
    registration_window = tk.Toplevel()
    registration_window.title("Register")
    registration_window.configure(bg='#101010')
    registration_window.geometry("400x400")  # Set a fixed size for the registration window

    tk.Label(registration_window, text="Email", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    email_entry = tk.Entry(registration_window, width=30, font="Helvetica 12")
    email_entry.pack(pady=5)

    tk.Label(registration_window, text="Password", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    password_entry = tk.Entry(registration_window, show='*', width=30, font="Helvetica 12")
    password_entry.pack(pady=5)

    tk.Label(registration_window, text="Confirm Password", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    confirm_password_entry = tk.Entry(registration_window, show='*', width=30, font="Helvetica 12")
    confirm_password_entry.pack(pady=5)

    tk.Button(registration_window, text="Register", command=lambda: register_user(email_entry.get(), password_entry.get(), confirm_password_entry.get()), bg='#ff3b3b', fg='white', font="Helvetica 14 bold", width=15).pack(pady=20)

    # Add login link with Text widget
    login_text = tk.Text(registration_window, height=1, width=40, bg='#101010', fg='white', font="Helvetica 12", borderwidth=0, highlightthickness=0)
    login_text.pack(pady=10)
    login_text.insert(tk.END, "If you already have an account, ")
    login_text.insert(tk.END, "click here to login.", 'login')
    login_text.tag_config('login', foreground='red', underline=True)

    # Bind click event to open login form
    login_text.bind("<Button-1>", lambda e: create_login_form())  
    # Change cursor to arrow when hovering over the text
    login_text.bind("<Enter>", lambda e: login_text.config(cursor="hand2"))
    login_text.bind("<Leave>", lambda e: login_text.config(cursor=""))  # Reset cursor when leaving

def create_admin_panel():
    """Create the admin panel."""
    admin_window = tk.Toplevel()
    admin_window.title("Admin Panel")
    admin_window.geometry("600x500")
    admin_window.configure(bg='#101010')

    tk.Label(admin_window, text="Admin Panel", bg='#101010', fg='white', font="Helvetica 16 bold").pack(pady=10)

    # Navigation Menu
    nav_frame = tk.Frame(admin_window, bg='#101010')
    nav_frame.pack(pady=10)

    tk.Button(nav_frame, text="Add Movie", command=lambda: add_movie_window(), bg='#ff3b3b', fg='white').pack(side=tk.LEFT, padx=5)
    tk.Button(nav_frame, text="Update Movie", command=lambda: update_movie_window(), bg='#ff3b3b', fg='white').pack(side=tk.LEFT, padx=5)
    tk.Button(nav_frame, text="Ticket Booking History", command=lambda: show_booking_history(), bg='#ff3b3b', fg='white').pack(side=tk.LEFT, padx=5)
    tk.Button(nav_frame, text="User  Login Details", command=lambda: show_user_details(), bg='#ff3b3b', fg='white').pack(side=tk.LEFT, padx=5)

def add_movie_window():
    """Open the Add Movie window."""
    add_movie_window = tk.Toplevel()
    add_movie_window.title("Add Movie")
    add_movie_window.geometry("500x500")
    add_movie_window.configure(bg='#101010')

    # Movie Title
    tk.Label(add_movie_window, text="Movie Title", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    movie_title_entry = tk.Entry(add_movie_window, width=30, font="Helvetica 12")
    movie_title_entry.pack(pady=5)

    # Genre
    tk.Label(add_movie_window, text="Genre", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    genre_var = tk.StringVar()
    genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Horror", "Sci-Fi", "Thriller"]
    genre_dropdown = ttk.Combobox(add_movie_window, textvariable=genre_var, values=genres, width=27, font="Helvetica 12")
    genre_dropdown.pack(pady=5)

    # Day Selection
    tk.Label(add_movie_window, text="Day", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    day_var = tk.StringVar()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_dropdown = ttk.Combobox(add_movie_window, textvariable=day_var, values=days, width=27, font="Helvetica 12")
    day_dropdown.pack(pady=5)

    # Add Movie Button
    tk.Button(add_movie_window, text="Add Movie", 
              command=lambda: add_movie_to_db(
                  movie_title_entry.get(), 
                  genre_var.get(),
                  day_var.get(),
                  add_movie_window
              ),
              bg='#ff3b3b', fg='white', font="Helvetica  14 bold", width=15).pack(pady=20)

def add_movie_to_db(title, genre, day, window):
    """Add a new movie to the database."""
    if not all([title, genre, day]):
        messagebox.showerror("Error", "All fields are required!")
        return

    conn = init_db()
    cursor = conn.cursor()
    try:
        # Insert into movies table without time_slot
        cursor.execute('''
            INSERT INTO movies (title, genre, day)
            VALUES (%s, %s, %s)
        ''', (title, genre, day))
        
        # Update weekly schedule
        if day in weekly_schedule:
            # Replace the last movie in the list with the new movie
            weekly_schedule[day][-1] = title  # Replace the last movie
        else:
            weekly_schedule[day] = [title]  # If the day doesn't exist, create a new entry
            
        # Update movies by genre
        movies_by_genre[title] = genre
        
        conn.commit()
        messagebox.showinfo("Success", "Movie added successfully!")
        
        # Refresh the movie display
        refresh_movie_display()
        
        window.destroy()
        
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error: {err}")
    finally:
        conn.close()

def refresh_movie_display():
    """Refresh the movie display for the current day."""
    global movies_frame
    for widget in movies_frame.winfo_children():
        widget.destroy()  # Clear the current movie display

    current_day = datetime.datetime.now().strftime("%A")  # Get the current day
    for idx, movie in enumerate(weekly_schedule[current_day]):
        create_movie_card(movies_frame, movie, idx)  # Recreate movie cards for the current day

def update_movie_window():
    """Open the Update Movie window."""
    update_window = tk.Toplevel()
    update_window.title("Update Movie")
    update_window.geometry("500x600")
    update_window.configure(bg='#101010')

    # Populate movie selection from movies_by_genre
    tk.Label(update_window, text="Select Movie", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    movie_var = tk.StringVar()
    movie_dropdown = ttk.Combobox(update_window, textvariable=movie_var, values=list(movies_by_genre.keys()), width=27, font="Helvetica 12")
    movie_dropdown.pack(pady=5)

    # New Title
    tk.Label(update_window, text="New Title", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    new_title_entry = tk.Entry(update_window, width=30, font="Helvetica 12")
    new_title_entry.pack(pady=5)

    # New Genre
    tk.Label(update_window, text="New Genre", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    genre_var = tk.StringVar()
    genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Horror", "Sci-Fi", "Thriller"]
    genre_dropdown = ttk.Combobox(update_window, textvariable=genre_var, values=genres, width=27, font="Helvetica 12")
    genre_dropdown.pack(pady=5)

    # New Day
    tk.Label(update_window, text="New Day", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    day_var = tk.StringVar()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_dropdown = ttk.Combobox(update_window, textvariable=day_var, values=days, width=27, font="Helvetica 12")
    day_dropdown.pack(pady=5)

    # Update Button
    tk.Button(update_window, text="Update Movie",
              command=lambda: update_movie_in_db(
                  movie_var.get(),
                  new_title_entry.get(),
                  genre_var.get(),
                  day_var.get(),
                  update_window
              ),
              bg='#ff3b3b', fg='white', font="Helvetica 14 bold", width=15).pack(pady=20)

def update_movie_in_db(old_title, new_title, new_genre, new_day, window):
    """Update movie details in database."""
    if not old_title:
        messagebox.showerror("Error", "Please select a movie to update!")
        return

    conn = init_db()
    cursor = conn.cursor()
    try:
        update_query = "UPDATE movies SET"
        update_values = []
        
        if new_title:
            update_query += " title = %s,"
            update_values.append(new_title)
            movies_by_genre[new_title] = new_genre
            
        if new_genre:
            update_query += " genre = %s,"
            update_values.append(new_genre)
            movies_by_genre[new_title] = new_genre
            
        if new_day:
            update_query += " day = %s,"
            update_values.append(new_day)
            # Update weekly schedule
            for day in weekly_schedule:
                if old_title in weekly_schedule[day]:
                    weekly_schedule[day].remove(old_title)
            if new_day in weekly_schedule:
                weekly_schedule[new_day].append(new_title)
            else:
                weekly_schedule[new_day] = [new_title]

        update_query = update_query.rstrip(',')
        update_query += " WHERE title = %s"
        update_values.append(old_title)
        
        cursor.execute(update_query, tuple(update_values))
        conn.commit()
        messagebox.showinfo("Success", "Movie updated successfully!")
        
        # Refresh the movie display
        refresh_movie_display()
        window.destroy()
        
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error: {err}")
    finally:
        conn.close()

def show_user_details():
    """Show user login details."""
    users_window = tk.Toplevel()
    users_window.title("User  Details")
    users_window.geometry("600x400")
    users_window.configure(bg='#101010')

    # Create Treeview
    tree = ttk.Treeview(users_window, columns=("User  ID", "Email"), show='headings')
    
    # Define column headings
    tree.heading("User  ID", text="User  ID")
    tree.heading("Email", text="Email")
    
    # Configure column widths
    tree.column("User  ID", width=80)
    tree.column("Email", width=250)
    tree.pack(pady=20, padx=20, fill='both', expand=True)

    # Add scrollbar
    scrollbar = ttk.Scrollbar(users_window, orient='vertical', command=tree.yview)
    scrollbar.pack(side='right', fill='y')
    tree.configure(yscrollcommand=scrollbar.set)

    # Fetch and display user details
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT user_id, email 
            FROM users 
            ORDER BY user_id DESC
        ''')
        for row in cursor.fetchall():
            tree.insert("", 'end', values=row)
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error: {err}")
    finally:
        conn.close()

def show_booking_history():
    """Show all booking history for all users."""
    history_window = tk.Toplevel()
    history_window.title("All Booking History")
    history_window.geometry("600x400")
    history_window.configure(bg='#101010')

    # Create Treeview
    tree = ttk.Treeview(history_window, columns=("ID", "Movie", "Seats", "Total Price"), show='headings')
    
    # Define column headings
    tree.heading("ID", text="Booking ID")
    tree.heading("Movie", text="Movie")
    tree.heading("Seats", text="Seats")
    tree.heading("Total Price", text="Total Price")

    # Configure column widths
    tree.column("ID", width=40)
    tree.column("Movie", width=100)
    tree.column("Seats", width=100)
    tree.column("Total Price", width=50)

    tree.pack(pady=20, padx=20, fill='both', expand=True)

    # Add scrollbar
    scrollbar = ttk.Scrollbar(history_window, orient='vertical', command=tree.yview)
    scrollbar.pack(side='right', fill='y')
    tree.configure(yscrollcommand=scrollbar.set)

    # Fetch and display all booking history
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, movie, seats, total_price 
            FROM booking_history 
            ORDER BY id DESC
        ''')
        for row in cursor.fetchall():
            tree.insert("", 'end', values=row)
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error: {err}")
    finally:
        conn.close()

def initialize_globals():
    """Initialize all global variables."""
    global movies_by_genre, weekly_schedule, time_slots, seat_buttons
    global selected_time_slot, time_slot_buttons, selected_movie, movie_posters

    movies_by_genre = {
        "Jurassic Park": "Adventure",
        "Fight Club": "Drama",
        "Back to the Future": "Adventure",
        "The Godfather": "Crime",
        "Transformers": "Action",
        "Batman": "Action",
        "Superman": "Action",
        "How to Train Your Dragon": "Animation",
        "The Hangover": "Comedy",
        "It": "Horror",
        "The Matrix": "Sci-Fi",
        "Interstellar": "Sci-Fi",
        "Arrival": "Sci-Fi",
        "A Quiet Place": "Horror",
        "Bird Box": "Thriller",
        "Smile": "Horror",
        "Hotel Transylvania": "Animation",
        "The Secret Life of Pets": "Animation",
        "Parasite": "Thriller",
        "Oldboy": "Thriller",
        "The Dictator": "Comedy",
        "Spider-Man": "Action",
        "Rocky": "Drama",
        "The Big Short": "Drama",
        "Dumb Money": "Drama",
        "The Founder ": "Biography",
        "Baby Driver": "Action",
        "Scarface": "Crime",
        "Mission Impossible": "Action",
        "Blade Runner": "Sci-Fi",
        "The Shawshank Redemption": "Drama",
        "The Conjuring": "Horror",
        "Paranormal Activity": "Horror"
    }

    weekly_schedule = {
        "Monday": ["The Matrix", "Batman", "Fight Club"],
        "Tuesday": ["Jurassic Park", "Interstellar", "The Godfather"],
        "Wednesday": ["Spider-Man", "The Shawshank Redemption", "Arrival"],
        "Thursday": ["Back to the Future", "Mission Impossible", "Parasite"],
        "Friday": ["Blade Runner", "The Big Short", "A Quiet Place"],
        "Saturday": ["How to Train Your Dragon", "The Hangover", "It"],
        "Sunday": ["Superman", "The Conjuring", "Rocky"]
    }
    
    time_slots = []  # Time slots removed
    seat_buttons = []
    selected_seats = []
    selected_time_slot = None
    time_slot_buttons = []
    selected_movie = None
    movie_posters = {}  # Will store posters only for current day's movies

def create_premium_button(parent, text, command, bg='#101010', fg='white', padx=10, pady=5):
    """Create a premium styled button with padding and colors."""
    button = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, font='Helvetica 12 bold', padx=padx, pady=pady)
    return button

def create_payment_form(seat_selection_window):
    """Create a payment form."""
    if not selected_time_slot:
        messagebox.showerror("Error", "Please select a time slot before proceeding to payment.")
        return

    if not selected_seats:
        messagebox.showerror("Error", "Please select at least one seat before proceeding to payment.")
        return

    payment_window = tk.Toplevel(seat_selection_window)
    payment_window.title("Payment Form")
    payment_window.configure(bg='#101010')
    payment_window.geometry("500x400")  # Increased size for the payment window

    total_price = len(selected_seats) * 120  # Calculate total price based on selected seats

    tk.Label(payment_window, text="Card Number", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    card_number_entry = tk.Entry(payment_window, width=30, font="Helvetica 12")
    card_number_entry.pack(pady=5)
    card_number_entry.config(validate="key")
    card_number_entry['validatecommand'] = (payment_window.register(lambda s: len(s) <= 16), '%P')

    tk.Label(payment_window, text="Expiration Date (YY-MM-DD)", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    expiration_entry = tk.Entry(payment_window, width=30, font="Helvetica 12")
    expiration_entry.pack(pady=5)

    tk.Label(payment_window, text="CVV", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)
    cvv_entry = tk.Entry(payment_window, show='*', width=30, font="Helvetica 12")
    cvv_entry.pack(pady=5)
    cvv_entry.config(validate="key")
    cvv_entry['validatecommand'] = (payment_window.register(lambda s: len(s) <= 3), '%P')

    tk.Label(payment_window, text=f"Total Price: {total_price}Rs.", bg='#101010', fg='white', font="Helvetica 14 bold").pack(pady=10)

    tk.Button(payment_window, text="Submit Payment", command=lambda: submit_payment(card_number_entry.get(), expiration_entry.get(), cvv_entry.get(), total_price, payment_window), bg='#ff3b3b', fg='white', font="Helvetica 14 bold", width=15).pack(pady=20)
    
def show_booking_confirmation(movie, seats, time):
    """Show booking confirmation window."""
    confirmation_window = tk.Toplevel()
    confirmation_window.title("Booking Confirmation")
    confirmation_window.configure(bg='#101010')
    confirmation_window.geometry("400x500")

    tk.Label(confirmation_window, text="Booking Confirmation", bg='#101010', fg='white', font="Helvetica 16 bold").pack(pady=10)

    # Movie Poster
    poster = fetch_movie_poster(movie)
    if poster:
        poster_label = tk.Label(confirmation_window, image=poster, bg='#101010')
        poster_label.image = poster  # Keep a reference to avoid garbage collection
        poster_label.pack(pady=(0, 10))

    # Movie Name
    tk.Label(confirmation_window, text=f"Movie: {movie}", bg='#101010', fg='white', font="Helvetica 14").pack(pady=5)

    # Selected Seats
    tk.Label(confirmation_window, text=f"Seats: {', '.join(seats)}", bg='#101010', fg='white', font="Helvetica 14").pack(pady=5)

    # Movie Time
    tk.Label(confirmation_window, text=f"Time: {time}", bg='#101010', fg='white', font="Helvetica 14").pack(pady=5)

    # Close Button
    tk.Button(confirmation_window, text="Close", command=confirmation_window.destroy, bg='#ff3b3b', fg='white', font="Helvetica 14 bold").pack(pady=20)

def submit_payment(card_number, expiration_date, cvv, total_price, payment_window):
    """Submit the payment details."""
    if not validate_payment_details(card_number, expiration_date, cvv):
        return

    # Save payment details to the database
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO payments (movie, seats, total_price, card_number, expiration_date, cvv, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (selected_movie, ', '.join(selected_seats), total_price, card_number, expiration_date, cvv, current_user_id))
        conn.commit()
        messagebox.showinfo("Payment Successful", "Your payment has been processed successfully!")
        
        # Save booking history
        save_booking_history()

        # Show booking confirmation
        show_booking_confirmation(selected_movie, selected_seats, selected_time_slot)

        # Close the payment window
        payment_window.destroy()

    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error: {err}")
    finally:
        conn.close()
        
def save_booking_history():
    """Save booking history to the database."""
    conn = init_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO booking_history (user_id, movie, seats, total_price)
            VALUES (%s, %s, %s, %s)
        ''', (current_user_id, selected_movie, ', '.join(selected_seats), len(selected_seats) * 120))
        conn.commit()
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error: {err}")
    finally:
        conn.close()

def validate_payment_details(card_number, expiration_date, cvv):
    """Validate payment details."""
    if len(card_number) != 16 or not card_number.isdigit():
        messagebox.showerror("Error", "Card number must be 16 digits.")
        return False

    if len(cvv) != 3 or not cvv.isdigit():
        messagebox.showerror("Error", "CVV must be 3 digits.")
        return False

    try:
        year, month, day = map(int, expiration_date.split('-'))
        if month < 1 or month > 12 or year < 0 or year > 99:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Expiration date must be in YY-MM-DD format.")
        return False

    return True

def create_time_buttons(parent):
    """Create time buttons for movie booking."""
    time_frame = tk.Frame(parent, bg='#101010')
    time_frame.pack(pady=10)

    time_slots = ["9:00 AM", "12:00 PM", "3:00 PM", "6:00 PM", "9:00 PM"]
    
    for idx, time in enumerate(time_slots):
        btn = tk.Button(time_frame, text=time, command=lambda t=time: select_time_slot(t), bg='#202020', fg='white', font="Helvetica 12 bold", width=10)
        btn.grid(row=0, column=idx, padx=5, pady=5)
        time_slot_buttons.append(btn)  # Store the button for later reference
        
def show_seat_selection_window():
    """Display the seat selection window."""
    global is_logged_in
    if not is_logged_in:
        messagebox.showwarning("Warning", "You must register or log in to book tickets.")
        create_registration_form()  # Prompt user to register first
        return

    if not selected_movie:
        messagebox.showwarning("Warning", "Please select a movie before proceeding.")
        return

    seat_selection_window = tk.Toplevel()
    seat_selection_window.title("Select Seats")
    seat_selection_window.configure(bg='#101010')

    tk.Label(seat_selection_window, text="Select your movie time:", font="Helvetica 16", bg='#101010', fg='white').pack(pady=10)

    create_time_buttons(seat_selection_window)  # Create time buttons

    tk.Label(seat_selection_window, text="Select your seats:", font="Helvetica 16", bg='#101010', fg='white').pack(pady=10)

    selected_seat_label = tk.Label(seat_selection_window, text="Selected Seats: None", font="Helvetica 12", bg='#101010', fg='white')
    selected_seat_label.pack(pady=10)

    # Create seat buttons
    for i in range(5):  # Example: 5 rows of seats
        row_frame = tk.Frame(seat_selection_window, bg='#101010')
        row_frame.pack(pady=5)
        for j in range(10):  # Example: 10 seats per row
            seat_btn = tk.Button(row_frame, text=f"Seat{i*10+j+1}", command=lambda seat=f"Seat{i*10+j+1}": select_seat(seat, selected_seat_label), bg='#28a745', fg='white', font='Helvetica 12', padx=10, pady=5)
            seat_btn.pack(side=tk.LEFT, padx=5)
            seat_buttons.append(seat_btn)

            # Add hover effect
            seat_btn.bind("<Enter>", lambda e, btn=seat_btn: btn.config(bg='#218838'))
            seat_btn.bind("<Leave>", lambda e, btn=seat_btn: btn.config(bg='#28a745'))

    payment_button = tk.Button(seat_selection_window, text="Proceed to Payment", command=lambda: create_payment_form(seat_selection_window), bg='#ff3b3b', fg='white', font='Helvetica 14 bold', padx=10, pady=5)
    payment_button.pack(pady=20)

def select_seat(seat, label):
    """Handle seat selection."""
    if seat in selected_seats:
        selected_seats.remove(seat)
        label.config(text=f"Selected Seats: {', '.join(selected_seats) if selected_seats else 'None'}")
        for btn in seat_buttons:
            if btn.cget("text") == seat:
                btn.config(bg='#28a745')  # Change back to available color
    else:
        selected_seats.append(seat)
        label.config(text=f"Selected Seats: {', '.join(selected_seats)}")
        for btn in seat_buttons:
            if btn.cget("text") == seat:
                btn.config(bg='#ffc107')  # Change to selected color

def toggle_seat(seat_num):
    """Toggle seat selection."""
    global selected_seats
    row = ord(seat_num[0]) - ord('A')
    col = int(seat_num[1]) - 1
    button = seat_buttons[row][col]
    
    if button['bg'] == '#202020':  # Available -> Selected
        button.config(bg='#ff3b3b')
        selected_seats.append(seat_num)
    elif button['bg'] == '#ff3b3b':  # Selected -> Available
        button.config(bg='#202020')
        selected_seats.remove(seat_num)

def center_window(window, width, height):
    """Center a window on the screen."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f'{width}x{height}+{x}+{y}')

def fetch_movie_poster(movie_title):
    """Fetch movie poster from OMDB API."""
    try:
        if movie_title in movie_posters:
            return movie_posters[movie_title]

        api_key = "7310d9c9"  # Replace with your actual API key
        url = f"http://www.omdbapi.com/?t={urllib.parse.quote(movie_title)}&apikey={api_key}"
        
        response = requests.get(url)
        movie_data = response.json()
        
        if movie_data.get('Poster') and movie_data['Poster'] != 'N/A':
            poster_response = requests.get(movie_data['Poster'])
            image = Image.open(BytesIO(poster_response.content))
            image = image.resize((200, 300), Image.LANCZOS)  # Corrected line
            movie_posters[movie_title] = ImageTk.PhotoImage(image)
            return movie_posters[movie_title]
        return None
    except Exception as e:
        print(f"Error fetching poster for {movie_title}: {e}")
        return None

def create_movie_card(parent, movie, idx):
    """Create a movie card with poster and details."""
    movie_frame = tk.Frame(parent, bg='#151515', padx=20, pady=15)
    movie_frame.grid(row=0, column=idx, padx=15)
    
    # Fetch poster for this specific movie
    poster = fetch_movie_poster(movie)
    if poster:
        poster_label = tk.Label(movie_frame, image=poster, bg='#151515')
        poster_label.pack(pady=(0, 10))
    
    btn = tk.Button(movie_frame, text=movie, width=25, height=2,
                   bg='#202020', fg='white', font="Helvetica 12 bold",
                   command=lambda m=movie: select_movie(m))
    btn.pack()
    
    genre_label = tk.Label(movie_frame, text=movies_by_genre[movie],
                         font="Helvetica 10", bg='#151515', fg='#888888')
    genre_label.pack(pady=(5, 0))

def create_premium_time_button(parent, time_slot, index):
    """Create an industrial-grade time slot button."""
    btn = tk.Button(parent, text=time_slot, width=12, height=2,
                   bg='#151515', fg='#cccccc', font="Helvetica 12",
                   bd=0, command=lambda: select_time_slot(time_slot, index))
    
    def on_enter(e):
        if index != selected_time_slot:
            btn.config(bg="#202020")
    
    def on_leave(e):
        if index != selected_time_slot:
            btn.config(bg='#151515')

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn

def select_time_slot(time_slot):
    """Handle time slot selection."""
    global selected_time_slot
    selected_time_slot = time_slot  # Store the selected time slot
    # Update button colors to indicate selection
    for btn in time_slot_buttons:
        if btn['text'] == time_slot:
            btn.config(bg='#ff3b3b')  # Highlight selected time slot
        else:
            btn.config(bg='#202020')  # Reset other buttons

def select_movie(movie):
    """Handle movie selection."""
    global selected_movie
    selected_movie = movie
    # Reset all movie buttons
    for widget in movies_frame.winfo_children():
        for child in widget.winfo_children():
            if isinstance(child, tk.Button):
                child.config(bg='#202020')
    # Highlight selected movie button
    for widget in movies_frame.winfo_children():
        for child in widget.winfo_children():
            if isinstance(child, tk.Button) and child['text'] == movie:
                child.config(bg='#ff3b3b')

def create_seat_layout(parent):
    """Create the seat selection layout."""
    seat_frame = tk.Frame(parent, bg='#080808')
    seat_frame.pack(pady=20)

    # Screen
    screen_label = tk.Label(seat_frame, text="SCREEN", bg='#1a1a1a', fg='#ffffff',
                           font="Helvetica 12 bold", width=60, height=2)
    screen_label.grid(row=0, column=0, columnspan=10, pady=(0, 40))

    # Seat layout
    rows = "ABCDEFGH"
    global seat_buttons
    seat_buttons = []

    for row_idx, row in enumerate(rows):
        # Row label
        tk.Label(seat_frame, text=row, font="Helvetica 12 bold", 
                bg='#080808', fg='#ffffff').grid(row=row_idx+1, column=0, padx=10)
        
        seat_row = []
        
        for col in range(8):
            seat_num = f"{row}{col+1}"
            btn = tk.Button(seat_frame, text=seat_num, width=6, height=2, bg='#202020', fg='white', font="Helvetica 10", command=lambda s=seat_num: toggle_seat(s))
            btn.grid(row=row_idx+1, column=col+1, padx=5, pady=5)
            seat_row.append(btn)
        seat_buttons.append(seat_row)

        # Add aisle after every second row
        if (col + 1) % 4 == 0:
            tk.Frame(seat_frame, width=20, bg='#080808').grid(row=row_idx+1, column=col+2)

    # Seat legend
    legend_frame = tk.Frame(seat_frame, bg='#080808')
    legend_frame.grid(row=len(rows)+2, column=0, columnspan=10, pady=30)

    # Available seat
    tk.Button(legend_frame, width=3, height=1, bg='#202020', state='disabled').pack(side='left', padx=10)
    tk.Label(legend_frame, text="Available", bg='#080808', fg='white', font="Helvetica 10").pack(side='left', padx=5)

    # Selected seat
    tk.Button(legend_frame, width=3, height=1, bg='#ff3b3b', state='disabled').pack(side='left', padx=10)
    tk.Label(legend_frame, text="Selected", bg='#080808', fg='white', font="Helvetica 10").pack(side='left', padx=5)

    # Booked seat
    tk.Button(legend_frame, width=3, height=1, bg='#666666', state='disabled').pack(side='left', padx=10)
    tk.Label(legend_frame, text="Booked", bg='#080808', fg='white', font="Helvetica 10").pack(side='left', padx=5)

    # Price information
    price_frame = tk.Frame(seat_frame, bg='#080808')
    price_frame.grid(row=len(rows)+3, column=0, columnspan=10, pady=20)
    
    tk.Label(price_frame, text="Price per seat: 120Rs.", 
            font="Helvetica 12 bold", bg='#080808', fg='#ffffff').pack()

    # Confirm booking button
    confirm_button = create_premium_button(seat_frame, "CONFIRM BOOKING", confirm_booking)
    confirm_button.grid(row=len(rows)+4, column=0, columnspan=10, pady=20)

def confirm_booking(seat_selection_window):
    """Handle booking confirmation."""
    if not selected_seats:
        messagebox.showerror("Error", "No seats selected.")
        return
    # Proceed to payment after confirming booking
    create_payment_form(seat_selection_window)
    seat_selection_window.destroy()  # Close the seat selection window

def create_main_widgets(root):
    """Create the main UI widgets with industrial-grade styling."""
    global movies_frame, time_slot_buttons, weekly_schedule, time_slots
    global login_button, register_button, logout_button

    root.attributes('-fullscreen', True)  # Set the window to full screen
    
    outer_frame = tk.Frame(root, bg='#080808')
    outer_frame.place(relwidth=1, relheight=1)
    
    pattern_canvas = tk.Canvas(outer_frame, bg='#080808', highlightthickness=0)
    pattern_canvas.place(relwidth=1, relheight=1)
    for i in range(0, 1440, 20):
        pattern_canvas.create_line(i,  0, i, 900, fill='#0a0a0a', width=1)
    for i in range(0, 900, 20):
        pattern_canvas.create_line(0, i, 1440, i, fill='#0a0a0a', width=1)

    main_frame = tk.Frame(outer_frame, bg='#101010', padx=140, pady=170)
    main_frame.place(relx=0.5, rely=0.5, anchor="center")

    # Header
    header_frame = tk.Frame(main_frame, bg='#101010')
    header_frame.grid(row=0, column=0, columnspan=7, pady=(0, 50))
    
    logo_text = tk.Label(header_frame, text="Movies Explore", font="Helvetica 60 bold", bg='#101010', fg='#ff3b3b')
    logo_text.pack()

    # Days of week
    current_day = datetime.datetime.now().strftime("%A")
    days_frame = tk.Frame(main_frame, bg='#101010')
    days_frame.grid(row=1, column=0, columnspan=7, pady=(0, 30))
    
    for idx, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
        day_color = '#ff3b3b' if day == current_day else '#666666'
        tk.Label(days_frame, text=day, font="Helvetica 14 bold", bg='#101010', fg=day_color).grid(row=0, column=idx, padx=20)

    # Movies for current day
    movies_frame = tk.Frame(main_frame, bg='#101010')
    movies_frame.grid(row=2, column=0, columnspan=7, pady=(0, 30))
    
    # Create movie cards for current day's movies
    for idx, movie in enumerate(weekly_schedule[current_day]):
        create_movie_card(movies_frame, movie, idx)

    # Booking button
    book_button = create_premium_button(main_frame, "BOOK NOW", show_seat_selection_window, bg='#ff1f1f', fg='white', padx=20, pady=10)
    book_button.grid(row=4, column=0, columnspan=7, pady=(20, 0))

    # Login and Registration Buttons
    login_button = create_premium_button(main_frame, "Login", create_login_form, bg='#101010', fg='red')  # Set background to match parent
    login_button.grid(row=0, column=6, pady=(0, 0), sticky='e')  # Adjusted position

    register_button = create_premium_button(main_frame, "Register", create_registration_form, bg='#101010', fg='red')  # Set background to match parent
    register_button.grid(row=0, column=7, pady=(0, 0), sticky='w')  # Adjusted position

    logout_button = create_premium_button(main_frame, "Logout", logout_user, bg='#101010', fg='red')  # Set background to match parent
    logout_button.grid(row=0, column=7, pady=(0, 0), sticky='w')  # Adjusted position
    logout_button.grid_forget()  # Initially hide the logout button

def main():
    """Main function to run the application."""
    initialize_globals()
    root = tk.Tk()
    root.title("Movies Explore")
    create_main_widgets(root)
    root.mainloop()

if __name__ == "__main__":
    main()
