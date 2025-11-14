# HostelBookingApp/app.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import datetime # Import datetime for timestamp

# --- 1. Initialize Flask App ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes, allowing your frontend to connect

# --- 2. Database Configuration ---
# Use SQLite for simplicity (file-based database)
# The database file 'bookings.db' will be created in your project directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Suppress a warning

db = SQLAlchemy(app)

# --- 3. Database Models ---
# Define the structure of your database tables as Python classes

# Model for Bookings
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, nullable=False)
    hostel_name = db.Column(db.String(100), nullable=False)
    checkin_date = db.Column(db.String(10), nullable=False) # Stored as YYYY-MM-DD string
    num_beds = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(100), nullable=True)
    user_email = db.Column(db.String(100), nullable=True)
    user_phone = db.Column(db.String(20), nullable=True) # New field for user phone
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow) # Use utcnow for consistency

    def __repr__(self):
        return f'<Booking {self.hostel_name} on {self.checkin_date} for {self.num_beds} beds by {self.user_name}>'

# Model for Hostels (to store hostel details, especially owner info)
class Hostel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_phone = db.Column(db.String(20), nullable=False)
    owner_email = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Hostel {self.name} by {self.owner_name}>'

# --- 4. API Routes (Endpoints) ---

@app.route('/')
def index():
    return "Hostel Booking Backend is running! Access /api/bookings for data."

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json() # Get JSON data sent from frontend

    # Basic validation of incoming data
    if not data:
        return jsonify({"error": "No data provided"}), 400
    required_fields = ['hostel_id', 'hostel_name', 'checkin_date', 'num_beds', 'user_name', 'user_email', 'user_phone']
    if not all(field in data for field in required_fields):
        missing = [field for field in required_fields if field not in data]
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    new_booking = Booking(
        hostel_id=data['hostel_id'],
        hostel_name=data['hostel_name'],
        checkin_date=data['checkin_date'],
        num_beds=data['num_beds'],
        user_name=data['user_name'],
        user_email=data['user_email'],
        user_phone=data['user_phone']
    )

    try:
        db.session.add(new_booking)
        db.session.commit()

        # --- Messaging Logic (Server-side Placeholder) ---
        # In a real application, this is where you'd send actual emails/SMS/WhatsApp
        # to the hostel owner and the user.
        # You would use libraries like 'smtplib' for email or 'Twilio' for SMS/WhatsApp.

        # Fetch owner info from the database (Hostel model)
        hostel = Hostel.query.get(data['hostel_id'])
        if hostel:
            print(f"\n--- NEW BOOKING NOTIFICATION ---")
            print(f"Hostel: {hostel.name}")
            print(f"Check-in Date: {data['checkin_date']}")
            print(f"Number of Beds: {data['num_beds']}")
            print(f"Booked by: {data['user_name']} ({data['user_email']}, {data['user_phone']})")
            print(f"Owner: {hostel.owner_name} (Phone: {hostel.owner_phone}, Email: {hostel.owner_email})")
            print(f"-----------------------------------\n")

            # Example of how you'd call a function to send a real email:
            # from your_mail_module import send_email
            # send_email(
            #     to_email=hostel.owner_email,
            #     subject=f"New Booking for {hostel.name} by {data['user_name']}",
            #     body=f"Details: {data['num_beds']} beds on {data['checkin_date']}. User: {data['user_name']} {data['user_phone']}."
            # )
            # send_email(
            #     to_email=data['user_email'],
            #     subject=f"Your Booking Confirmation for {hostel.name}",
            #     body=f"Hi {data['user_name']},\nYour booking for {data['num_beds']} beds at {hostel.name} on {data['checkin_date']} is confirmed."
            # )
        else:
            print(f"WARNING: Could not find owner info for hostel_id {data['hostel_id']} in DB.")


        return jsonify({"message": "Booking created successfully!", "booking_id": new_booking.id}), 201
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        print(f"Error creating booking: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    # Fetch all bookings from the database
    bookings = Booking.query.order_by(Booking.timestamp.desc()).all()
    # Convert list of Booking objects to a list of dictionaries for JSON response
    output = []
    for booking in bookings:
        output.append({
            'id': booking.id,
            'hostel_id': booking.hostel_id,
            'hostel_name': booking.hostel_name,
            'checkin_date': booking.checkin_date,
            'num_beds': booking.num_beds,
            'user_name': booking.user_name,
            'user_email': booking.user_email,
            'user_phone': booking.user_phone,
            'timestamp': booking.timestamp.isoformat() # Convert datetime object to ISO format string
        })
    return jsonify(output)

@app.route('/api/hostels', methods=['GET'])
def get_hostels():
    # Fetch all hostels from the database
    hostels = Hostel.query.all()
    output = []
    for hostel in hostels:
        output.append({
            'id': hostel.id,
            'name': hostel.name,
            'address': hostel.address,
            'price': hostel.price,
            'rating': hostel.rating,
            'owner': {
                'name': hostel.owner_name,
                'phone': hostel.owner_phone,
                'email': hostel.owner_email
            }
            # You might want to add images, features, menu, timings, reviews from your frontend data
            # For simplicity, we're keeping the DB model basic for now.
            # In a real app, these might be separate tables or JSONB columns.
        })
    return jsonify(output)

# --- 5. Run the Flask App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables based on models if they don't exist
        # Add initial hostel data if the Hostel table is empty
        if Hostel.query.count() == 0:
            print("Adding initial hostel data...")
            initial_hostels = [
                Hostel(id=1, name='The Boys Hostel', address='Kandalakoya, 501401', price=5500, rating=4.5,
                       owner_name='Mr. Vijay Mama', owner_phone='+916305464572', owner_email='theboyshostel@gmail.com'),
                Hostel(id=2, name='Ganesh Girls Hostel', address='kandlakoya near CMR Techinal Campus', price=6000, rating=4.2,
                       owner_name='Mr. Ganesh Nayak', owner_phone='+919876543210', owner_email='ganeshgirlshostel@gmail.com'),
                Hostel(id=3, name='Co-Live In Hostel', address='kandalkoya, Medchal', price=7000, rating=4.8,
                       owner_name='Dheeraj', owner_phone='+918765432109', owner_email='co-livein@gmail.com'),
                Hostel(id=4, name='Hostel', address='kandalkoya, Medchal', price=7000, rating=4.8,
                       owner_name='Dheeraj', owner_phone='+918765432109', owner_email='co-livein@gmail.com')
            ]
            db.session.bulk_save_objects(initial_hostels)
            db.session.commit()
            print("Initial hostel data added.")
    app.run(debug=True) # debug=True enables auto-reload and useful error messages