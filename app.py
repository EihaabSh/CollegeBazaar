from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from pymongo import MongoClient
import pymongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import boto3
from bson import ObjectId
from io import BytesIO
from PIL import Image
import certifi
from datetime import datetime
import uuid
from urllib.parse import urlparse
app = Flask(__name__)




# Load environment variables from .env file
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
uri = os.getenv("uri")
app.secret_key = os.getenv("app.secret_key")



# Initialize the S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    
)



client = pymongo.MongoClient(
    uri,
    tlsCAFile=certifi.where()
)

# Connect to a specific database
db = client['CollegeBazaar']  # Replace with your actual database name
posts_collection = db['posts']  # Replace with your collection name
users_collection = db['users']  # Database for the users info
messages_collection = db['messages'] # database for the messages



# helps for auto deletion of the messages sent
messages_collection.create_index("timestamp", expireAfterSeconds=604800)  # 7 days = 604800 seconds


# List of Canadian university domains
domains = {
    "acadiau.ca": "Acadia University", "algomau.ca": "Algoma University", 
    "ubishops.ca": "Bishop's University", "brandonu.ca": "Brandon University", 
    "capu.ca": "Cape Breton University", "carleton.ca": "Carleton University", 
    "centennialcollege.ca": "Centennial College", "usb.ca": "University of St. Boniface", 
    "concordia.ca": "Concordia University", "dal.ca": "Dalhousie University", 
    "domuni.ca": "Dominican University College", "douglascollege.ca": "Douglas College", 
    "durhamcollege.ca": "Durham College", "ecuad.ca": "Emily Carr University of Art + Design", 
    "polymtl.ca": "École Polytechnique de Montréal", "fanshawec.ca": "Fanshawe College", 
    "humber.ca": "Humber College", "icmanitoba.ca": "International College of Manitoba", 
    "lakeheadu.ca": "Lakehead University", "laurentian.ca": "Laurentian University", 
    "ulaval.ca": "Université Laval", "macewan.ca": "MacEwan University", "mcgill.ca": "McGill University", 
    "mcmaster.ca": "McMaster University", "mun.ca": "Memorial University of Newfoundland", 
    "mta.ca": "Mount Allison University", "mtroyal.ca": "Mount Royal University", 
    "nipissingu.ca": "Nipissing University", "ocadu.ca": "Ontario College of Art and Design University", 
    "ontariotechu.ca": "Ontario Tech University", "umontreal.ca": "Université de Montréal", 
    "usherbrooke.ca": "Université de Sherbrooke", "uqam.ca": "Université du Québec à Montréal", 
    "queensu.ca": "Queen's University", "rdpolytech.ca": "Red Deer Polytechnic", 
    "royalroads.ca": "Royal Roads University", "torontomu.ca": "Toronto Metropolitan University", 
    "smu.ca": "Saint Mary's University", "sfu.ca": "Simon Fraser University", 
    "stfx.ca": "St. Francis Xavier University", "stu.ca": "St. Thomas University", 
    "tru.ca": "Thompson Rivers University", "tyndale.ca": "Tyndale University", 
    "ualberta.ca": "University of Alberta", "ubc.ca": "University of British Columbia", 
    "ucalgary.ca": "University of Calgary", "uoguelph.ca": "University of Guelph", 
    "uottawa.ca": "University of Ottawa", "upei.ca": "University of Prince Edward Island", 
    "uregina.ca": "University of Regina", "usask.ca": "University of Saskatchewan", 
    "utoronto.ca": "University of Toronto", "uvic.ca": "University of Victoria", 
    "uwaterloo.ca": "University of Waterloo", "uwo.ca": "Western University", 
    "uwinnipeg.ca": "University of Winnipeg", "viu.ca": "Vancouver Island University", 
    "yorku.ca": "York University", "my.yorku.ca": "York University", "my.unt.edu": "University of North Texas",
    "student.london.ac.uk" : "University of London"
}


# Displaying the front page of the website
@app.route('/')
def home():
    return render_template('index.html')

# Sending the user's email information to the database
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        University_email = request.form['University_email']
        password = request.form['password']
        
        user = users_collection.find_one({'University_email': University_email})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['University'] = user['University']  # Retrieve university from the database
            session['username_extracted'] = user['username_extracted']
            session['University_email'] = user['University_email']
            return redirect(url_for('dashboard', University=user['University']))
        
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        University_email = request.form['University_email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        print(f"Password: {password}, Confirm Password: {confirm_password}")

        if password != confirm_password:
            
            return redirect(url_for('register'))
            
        # Storing the username for the user from their email
        username_extracted = University_email.split('@')[0]
        
        # Extracting their domain in order to check if it is a valid university email 
        domain_extracted = University_email.split('@')[1]
        if domain_extracted not in domains:
            flash('Invalid domain. Registration is restricted to specific university domains.')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Check if the user already exists
        existing_user = users_collection.find_one({'University_email': University_email})
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))
        
        # Insert new user into MongoDB
        users_collection.insert_one({
            'University_email': University_email,
            'username_extracted': username_extracted,
            'password': hashed_password,
            'University': domain_extracted
        })
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('home'))
    
    return render_template('index.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clears all session data
    return redirect(url_for('login'))  # Redirect to login page after logout


# for creating a post
@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    print("works")
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        description = request.form['description']
        phone = request.form['phone']
        user_id = session['user_id']
        University = session['University']
        username_extracted = session['username_extracted']
        University_email = session['University_email']
        
        print("works")
        
        picture_url = None
        file = request.files.get('picture')
        file_extension = file.filename.split('.')[-1]  
        unique_filename = f"{uuid.uuid4()}.{file_extension}"  # Use uuid4() from the uuid module
        
        s3_key = f"uploads/{unique_filename}"
        img = Image.open(file)
        # Store the format in a variable
        image_format = img.format
        if image_format == 'JPEG':
            jpeg_stream = BytesIO()
            # convertion to jpeg
            converted = img.convert("RGB")
            converted.save(jpeg_stream, format='JPEG', quality=20, optimize=True)
            jpeg_stream.seek(0)
            print(len(jpeg_stream.getvalue()))
            s3.upload_fileobj(jpeg_stream, AWS_BUCKET_NAME, s3_key, ExtraArgs={
                "ACL": "public-read",
                
            },)
        elif image_format == 'PNG':
            
            png_stream = BytesIO()
            img.save(png_stream, format='PNG', optimize=True)
            png_stream.seek(0)
            s3.upload_fileobj(png_stream, AWS_BUCKET_NAME, s3_key, ExtraArgs={
                "ACL": "public-read",
                
            },)
                
        
        picture_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        
    
        print("works")
        # Insert the post into the database
        posts_collection.insert_one({
            'name': name,
            'category': category,
            'price': price,
            'description': description,
            'user_id': user_id,
            'username_extracted': username_extracted,
            'University': University,
            'created_at': datetime.now(),
            'picture_url': picture_url,
            'University_email': University_email,
            'phone': phone
        })
        print("works")
        return redirect(url_for('dashboard', University=University))
    
    return render_template('createposts.html')



# Displaying the user posts from MongoDB
@app.route('/dashboard/<University>', methods=['POST', 'GET'])
def dashboard(University):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    print("works")
    
    page = int(request.form.get('page', 1))  # Current page number from form
   
    limit = 8
   
    print("works")
    
    if request.method == 'POST':
        x = request.form['submit_button']
        
 
        if x == 'Action1':
            limit = page * limit
        

    uni = domains.get(University)
    posts = list(posts_collection.find({'University': University}).limit(limit))
    print(posts)
    shower = len(posts) == limit
    return render_template('dashboard.html', posts=posts, University=University, uni=uni, page=page, shower=shower)

@app.route('/X/<University>', methods=['POST', 'GET'])
def X(University):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    page = int(request.args.get('page', 1))  # Get page from query params
    limit = 8
    
    # Calculate total items to fetch based on page number
    total_limit = page * limit
    
    # Fetch posts with the calculated limit
    posts = list(posts_collection.find({'University': University}).limit(total_limit))
    
    # Check if there are more posts to show
    shower = len(posts) == total_limit
    
    return render_template('X.html', posts=posts, shower=shower)
    
    
   
   
    
    

# this is for the search bar and filter
@app.route('/search/<University>', methods=['POST', 'GET'])
def search(University):
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    
    query = {'University' : University}
    
    
    if request.method == 'GET':
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        print(category)
        print("1")
        session['search'] = search
        session['category'] = category

    if search:
        query['name'] = {'$regex': search, '$options': 'i'}
    if category and category != 'All':
        query['category'] = category
        
    page = int(request.form.get('page', 1))  # Current page number from form
    limit = 8
    print("works")
    
    if request.method == 'POST':
        x = request.form['submit_button']
    
    
        if x == 'Action1':
            limit = page * limit
    
    
    searches = posts_collection.find(query)
    categories = posts_collection.distinct('category')
    
    uni = domains.get(University) 
    
    return render_template('search.html', searches=searches, categories=categories, University=University, uni=uni, page=page)

    


    

# Delete the user's post
@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    posts = posts_collection.find_one({'_id': ObjectId(post_id)})
    post = posts_collection.find_one({'_id': ObjectId(post_id)}, {"_id": 0, "picture_url": 1})
    parsed_url = urlparse(post['picture_url'])  # Pass the picture_url field
    object_key = parsed_url.path.lstrip('/')  # Remove leading slash to get the object key
    print(f"Picture URL: {post['picture_url']}")
    print(f"Object Key: {object_key}")

    bucket_name = 'thecollegebazaar'
    try:
        # Attempt to delete the object from S3
        response = s3.delete_object(Bucket=bucket_name, Key=object_key)
        print(f"Delete response: {response}")
        print(f"Successfully deleted object from S3: {object_key}")
    except Exception as e:
        print(f"Error deleting object from S3: {e}")

    if posts and posts['user_id'] == user_id:
        posts_collection.delete_one({'_id': ObjectId(post_id)})
        return redirect(url_for('profile'))
    
    return redirect(url_for('profile'))


# Displaying the profile when the user clicks on their profile
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    print("39")
    user_id = session['user_id']
    posts = posts_collection.find({'user_id': user_id})
    
    print("32")
    return render_template('profile.html', posts=posts)

# Sends the user back to the index when "theCollegeBazaar" is clicked on
@app.route('/index')
def home1():
    return render_template('index.html') 

@app.route('/post/<post_id>')
def post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Fetch posts that belong to the user's university
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    
    return render_template('posts.html', post=post)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')



#//////////////////////////////////////////////////////////////////////////////////////////////////

# Route to view the messages page
@app.route('/message/<post_id>', methods=['GET', 'POST'])
def message(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    seller_id = post.get('user_id')
    
    sender_id = session['user_id']

    # Handle sending a message via POST
    if request.method == 'POST':
        message_text = request.form['message']
        new_message = {
            "sender_id": sender_id,
            "receiver_id": seller_id,
            "message": message_text,
            "timestamp": datetime.utcnow()
        }
        # Store message in MongoDB
        messages_collection.insert_one(new_message)

    # Fetch previous chat messages between buyer and seller
    chat_messages = list(messages_collection.find({
        "$or": [
            {"sender_id": sender_id, "receiver_id": seller_id},
            {"sender_id": seller_id, "receiver_id": sender_id}
        ]
    }).sort("timestamp", 1))

    return render_template('messages.html', chat=chat_messages, seller_id=seller_id)







    
    
        





    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
