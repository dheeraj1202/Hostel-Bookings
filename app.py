# HostelBookingApp/app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import datetime

# --- 1. Initialize Flask App ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_here' # Needed for flash messages

# --- 2. Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 3. Database Models ---

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, nullable=False)
    hostel_name = db.Column(db.String(100), nullable=False)
    checkin_date = db.Column(db.String(10), nullable=False) # Store as YYYY-MM-DD string
    num_beds = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    user_phone = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Booking {self.hostel_name} on {self.checkin_date} for {self.num_beds} beds by {self.user_name}>'

class Hostel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_phone = db.Column(db.String(20), nullable=False)
    owner_email = db.Column(db.String(100), nullable=False)
#in a large app thesr might be seperate tables or more complex structrue ina a
    # In a larger app, these might be separate tables or more complex structures
    images_json = db.Column(db.Text, nullable=True) # Store as JSON string
    features_json = db.Column(db.Text, nullable=True)
    menu_json = db.Column(db.Text, nullable=True)
    timings_json = db.Column(db.Text, nullable=True)
    reviews_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Hostel {self.name} by {self.owner_name}>'

    # Helper methods to convert JSON strings back to Python objects
    def get_images(self):
        import json
        return json.loads(self.images_json) if self.images_json else []
    def get_features(self):
        import json
        return json.loads(self.features_json) if self.features_json else []
    def get_menu(self):
        import json
        return json.loads(self.menu_json) if self.menu_json else {}
    def get_timings(self):
        import json
        return json.loads(self.timings_json) if self.timings_json else []
    def get_reviews(self):
        import json
        return json.loads(self.reviews_json) if self.reviews_json else []


# --- 4. Routes (Page Rendering and Form Handling) ---

@app.route('/')
def index():
    # Fetch all hostels to display on the home page
    all_hostels = Hostel.query.all()
    return render_template('index.html', hostels=all_hostels)

@app.route('/hostel/<int:hostel_id>')
def hostel_detail(hostel_id):
    hostel = db.session.get(Hostel, hostel_id) # Safer way to get by PK
    if not hostel:
        flash('Hostel not found!')
        return redirect(url_for('index'))
    return render_template('hostel_detail.html', hostel=hostel)


@app.route('/book/<int:hostel_id>', methods=['GET', 'POST'])
def book_bed(hostel_id):
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        flash('Hostel not found!')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Process the booking form submission
        user_name = request.form.get('user_name')
        user_email = request.form.get('user_email')
        user_phone = request.form.get('user_phone')
        checkin_date = request.form.get('checkin_date')
        num_beds_str = request.form.get('num_beds')

        # Basic validation
        if not all([user_name, user_email, user_phone, checkin_date, num_beds_str]):
            flash('Please fill in all required fields.')
            return render_template('booking_form.html', hostel=hostel, current_date=datetime.date.today().isoformat())
        
        try:
            num_beds = int(num_beds_str)
            if num_beds <= 0:
                raise ValueError("Number of beds must be positive.")
        except ValueError:
            flash('Number of beds must be a positive integer.')
            return render_template('booking_form.html', hostel=hostel, current_date=datetime.date.today().isoformat())

        new_booking = Booking(
            hostel_id=hostel.id,
            hostel_name=hostel.name,
            checkin_date=checkin_date,
            num_beds=num_beds,
            user_name=user_name,
            user_email=user_email,
            user_phone=user_phone
        )

        try:
            db.session.add(new_booking)
            db.session.commit()
            flash('Booking confirmed successfully!')

            # --- Messaging Logic (Server-side Placeholder) ---
            # This is where you'd integrate sending actual emails/SMS/WhatsApp.
            # print statements go to your Flask console.
            print(f"\n--- NEW BOOKING NOTIFICATION ---")
            print(f"Hostel: {hostel.name}")
            print(f"Check-in Date: {checkin_date}")
            print(f"Number of Beds: {num_beds}")
            print(f"Booked by: {user_name} ({user_email}, {user_phone})")
            print(f"Owner: {hostel.owner_name} (Phone: {hostel.owner_phone}, Email: {hostel.owner_email})")
            print(f"-----------------------------------\n")

            return redirect(url_for('booking_confirmation', booking_id=new_booking.id))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during booking: {e}')
            return render_template('booking_form.html', hostel=hostel, current_date=datetime.date.today().isoformat())

    # If GET request, just show the booking form
    return render_template('booking_form.html', hostel=hostel, current_date=datetime.date.today().isoformat())

@app.route('/booking_confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        flash('Booking not found.')
        return redirect(url_for('index'))

    hostel = db.session.get(Hostel, booking.hostel_id)
    if not hostel: # Fallback if hostel somehow not found for booking
        flash('Hostel details for this booking not found.')
        return redirect(url_for('index'))

    # Prepare data for rendering confirmation page
    checkin_date_formatted = datetime.datetime.strptime(booking.checkin_date, '%Y-%m-%d').strftime('%B %d, %Y')
    
    # Generate Google Maps URL
    encoded_address = hostel.address.replace(' ', '+') # Simple encoding for map URL
    Maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"

    # Generate WhatsApp message link (pre-filled message)
    # Note: wa.me links require country code without '+' or '00'
    owner_phone_cleaned = hostel.owner_phone.replace('+', '').replace(' ', '')
    whatsapp_text = f"Hello {hostel.owner_name},\n\nI just confirmed a booking for {booking.num_beds} bed(s) at {hostel.name} for check-in on {checkin_date_formatted}.\nMy name is {booking.user_name}, email is {booking.user_email}, and phone is {booking.user_phone}.\n\nLooking forward to hearing from you!\n\nRegards,\n{booking.user_name}"
    whatsapp_url = f"https://wa.me/{owner_phone_cleaned}?text={whatsapp_text}"

    # Generate Email message link (pre-filled subject and body)
    email_subject = f"Hostel Bed Booking Inquiry - {hostel.name}"
    email_body = f"Dear {hostel.owner_name},\n\nI am writing to inquire about booking {booking.num_beds} bed(s) at your hostel, {hostel.name}, for the check-in date of {checkin_date_formatted}.\n\nPlease let me know about the availability and the next steps for confirming this booking.\n\nThank you,\n{booking.user_name}\n{booking.user_phone}"
    email_url = f"mailto:{hostel.owner_email}?subject={email_subject}&body={email_body}"


    return render_template('booking_confirmation.html',
                           booking=booking,
                           hostel=hostel,
                           checkin_date_formatted=checkin_date_formatted,
                           Maps_url=Maps_url,
                           whatsapp_url=whatsapp_url,
                           email_url=email_url)

# --- 5. Run the Flask App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables if they don't exist
        # Add initial hostel data if the Hostel table is empty
        if Hostel.query.count() == 0:
            import json # Import json for storing complex data as strings
            print("Adding initial hostel data...")
            initial_hostels = [
                Hostel(id=1, name='The Boys Hostel', address='Kandalakoya, 501401', price=5500, rating=4.5,
                       owner_name='Mr. Vijay Mama', owner_phone='+916305464572', owner_email='theboyshostel@gmail.com',
                       images_json=json.dumps([
                           '/static/photos/337620911.jpg',
                           '/static/photos/New-Delhi_Miscellaneous_goStops-Hostel-Photo-Credit-goStops-e1594805675993.jpg',
                           '/static/photos/buliding.jpg'
                       ]),
                       features_json=json.dumps([
                           {'icon': 'wifi', 'text': 'High-Speed Wi-Fi'},
                           {'icon': 'fan', 'text': 'Air Conditioning'},
                           {'icon': 'lock', 'text': 'Personal Lockers'},
                           {'icon': 'shower-head', 'text': 'Hot Showers 24/7'},
                           {'icon': 'tv', 'text': 'Common TV Area'},
                       ]),
                       menu_json=json.dumps({
                           'breakfast': 'Pulihora, Idli , Vada , Dosa , Bonda , Chapathi .',
                           'lunch': 'All types of vegatables, Curd.',
                           'dinner': 'Veg currys, Wednesday, Sunday - chicken, Tuesday, Friday- Egg.'
                       }),
                       timings_json=json.dumps([
                           {'key': 'Main Gate Closing', 'value': '11:00 PM'},
                           {'key': 'Breakfast', 'value': '7:30 AM - 9:30 AM'},
                           {'key': 'Lunch', 'value': '12:30 PM - 2:30 PM'},
                           {'key': 'Dinner', 'value': '7:30 PM - 9:30 PM'}
                       ]),
                       reviews_json=json.dumps([
                           {'name': 'Anjali Rao', 'rating': 4, 'text': 'Great location and very clean. The staff is friendly and helpful. The food was surprisingly good!', 'avatar': 'AR'},
                           {'name': 'Vikram Singh', 'rating': 5, 'text': 'An absolutely fantastic stay. The beds are comfortable, and the common area is vibrant.', 'avatar': 'VK'}
                       ])
                ),
                Hostel(id=2, name='Ganesh Girls Hostel', address='kandlakoya near CMR Techinal Campus', price=6000, rating=4.2,
                       owner_name='Mr. Ganesh Nayak', owner_phone='+919876543210', owner_email='ganeshgirlshostel@gmail.com',
                       images_json=json.dumps([
                           '/static/photos/g31.png',
                           '/static/photos/bed.jpg',
                           '/static/photos/g1.jpg',
                       ]),
                       features_json=json.dumps([
                           {'icon': 'wifi', 'text': 'Free Wi-Fi'},
                           {'icon': 'coffee', 'text': '24/7 Coffee Bar'},
                           {'icon': 'lock', 'text': 'Secure Lockers'},
                           {'icon': 'shower-head', 'text': 'Hot Showers'},
                           {'icon': 'washing-machine', 'text': 'Laundry Service'},
                           {'icon': 'gym', 'text': 'GYM service'},
                       ]),
                       menu_json=json.dumps({
                           'breakfast': 'Pulihora, Idli , Vada , Dosa , Bonda , Chapathi, Oats, Paratha, Dosa, Juice.',
                           'lunch': 'Veg Thali, Rice, Mixed Veg.',
                           'dinner': 'Chicken Curry (opt.), Paneer Butter Masala, Rice.'
                       }),
                       timings_json=json.dumps([
                           {'key': 'Main Gate Closing', 'value': '10:00 PM'},
                           {'key': 'Breakfast', 'value': '8:00 AM - 10:00 AM'},
                           {'key': 'Lunch', 'value': '12:30 PM - 2:30 PM'},
                           {'key': 'Dinner', 'value': '7:30 PM - 9:30 PM'}
                       ]),
                       reviews_json=json.dumps([
                           {'name': 'Priya Sharma', 'rating': 5, 'text': 'Loved the vibe here! The food like at Hoome.', 'avatar': 'PS'}
                       ])
                ),
                Hostel(id=3, name='Co-Live In Hostel', address='kandalkoya, Medchal', price=7000, rating=4.8,
                       owner_name='Dheeraj', owner_phone='+918765432109', owner_email='co-livein@gmail.com',
                       images_json=json.dumps([
                           '/static/photos/room.avif',
                           '/static/photos/library.jpg',
                           '/static/photos/w1.jpeg',
                       ]),
                       features_json=json.dumps([
                           {'icon': 'wifi', 'text': 'Fiber Optic Wi-Fi'},
                           {'icon': 'book', 'text': 'Extensive Library'},
                           {'icon': 'lamp-desk', 'text': 'Study Desks'},
                           {'icon': 'washing-machine', 'text': 'Laundry Service'},
                           {'icon': 'lock', 'text': 'High-Security Lockers'},
                           {'icon': 'air-vent', 'text': 'Central AC'},
                       ]),
                       menu_json=json.dumps({
                           'breakfast': 'Continental & Indian mix, Fresh fruits, Milk.',
                           'lunch': 'Indian Thali.',
                           'dinner': 'Specialty Dinner, Roti, Rice, Dal, Dessert.'
                       }),
                       timings_json=json.dumps([
                           {'key': 'Main Gate Closing', 'value': '10:00 PM'},
                           {'key': 'Breakfast', 'value': '8:00 AM - 10:00 AM'},
                           {'key': 'Lunch', 'value': '12:30 PM - 2:30 PM'},
                           {'key': 'Dinner', 'value': '7:30 PM - 9:30 PM'}
                       ]),
                       reviews_json=json.dumps([
                           {'name': 'Shruthi', 'rating': 5, 'text': 'Perfect for students and remote workers. The internet is very fast and it\'s very quiet.', 'avatar': 'AD'},
                           {'name': 'Ammu', 'rating': 4.4, 'text': 'Best for co-livein and safe', 'avatar': 'AD'}
                       ])
                ),
                 Hostel(id=4, name='Hostel', address='kandalkoya, Medchal', price=7000, rating=4.8,
                       owner_name='Dheeraj', owner_phone='+918765432109', owner_email='co-livein@gmail.com',
                       images_json=json.dumps([
                           '/static/photos/w1.jpeg',
                           '/static/photos/room.avif',
                           '/static/photos/library.jpg',
                           '/static/photos/w1.jpeg',
                       ]),
                       features_json=json.dumps([
                           {'icon': 'wifi', 'text': 'Fiber Optic Wi-Fi'},
                           {'icon': 'book', 'text': 'Extensive Library'},
                           {'icon': 'lamp-desk', 'text': 'Study Desks'},
                           {'icon': 'washing-machine', 'text': 'Laundry Service'},
                           {'icon': 'lock', 'text': 'High-Security Lockers'},
                           {'icon': 'air-vent', 'text': 'Central AC'},
                       ]),
                       menu_json=json.dumps({
                           'breakfast': 'Continental & Indian mix, Fresh fruits, Milk.',
                           'lunch': 'Indian Thali.',
                           'dinner': 'Specialty Dinner, Roti, Rice, Dal, Dessert.'
                       }),
                       timings_json=json.dumps([
                           {'key': 'Main Gate Closing', 'value': '10:00 PM'},
                           {'key': 'Breakfast', 'value': '8:00 AM - 10:00 AM'},
                           {'key': 'Lunch', 'value': '12:30 PM - 2:30 PM'},
                           {'key': 'Dinner', 'value': '7:30 PM - 9:30 PM'}
                       ]),
                       reviews_json=json.dumps([
                           {'name': 'Shruthi', 'rating': 5, 'text': 'Perfect for students and remote workers. The internet is very fast and it\'s very quiet.', 'avatar': 'AD'},
                           {'name': 'Ammu', 'rating': 4.4, 'text': 'Best for co-livein and safe', 'avatar': 'AD'}
                       ])
                )
            ]
            db.session.bulk_save_objects(initial_hostels)
            db.session.commit()
            print("Initial hostel data added.")
    app.run(debug=True)