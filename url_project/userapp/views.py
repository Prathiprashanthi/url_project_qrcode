from django.shortcuts import render,redirect
from django.contrib import messages
from mainapp.models import *
from userapp.models import *
from adminapp.models import *
import math, random
import qrcode
from PIL import Image, ImageDraw
from io import BytesIO
from django.core.files import File
import time
import pytz
from datetime import datetime
import string
import re
from nltk.stem import WordNetLemmatizer
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer()

# Create your views here.
def user_index(request):
    images_count = UserModel.objects.all().count()
    print(images_count)
    user_id = request.session["user_id"]
    user = UserModel.objects.get(user_id = user_id)
    prediction_count =  UserModel.objects.all().count()
    
    if user.Last_Login_Time is None:
        IST = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(IST).time()
        user.Last_Login_Time = current_time_ist
        user.save()
        messages.success(request, 'You are login SUccessfully..')
    return render(request,'user/user-index.html', {'detect' : images_count, 'la' : user,'predictions' : prediction_count,})
from datetime import datetime

def user_myprofile(request):
    user_id = request.session["user_id"]
    user = UserModel.objects.get(user_id = user_id)
    if request.method == 'POST':
        user_name = request.POST.get('name')
        user_age = request.POST.get('age')
        user_phone = request.POST.get('contact')
        user_email = request.POST.get('email')
        user_address = request.POST.get("address")
        
        # user_img = request.POST.get("userimg")

        user.user_name = user_name
        user.user_age = user_age
        user.user_address = user_address
        user.user_contact = user_phone
        user.user_email=user_email
       

        if len(request.FILES) != 0:
            image = request.FILES['image']
            user.user_image = image
            user.user_name = user_name
            user.user_age = user_age
            user.user_contact = user_phone
            user.user_email=user_email
            user.user_address = user_address
            user.save()
            messages.success(request, 'Updated SUccessfully...!')
        else:
            user.user_name = user_name
            user.user_age = user_age
            user.save()
            messages.success(request, 'Updated SUccessfully...!')
            
    context = {"i":user}
    return render(request, 'user/user-myprofile.html',context)


import qrcode
from PIL import Image
from io import BytesIO
import pickle
from nltk.stem import WordNetLemmatizer
import re
import string
from django.urls import reverse
import json
  # Assuming you have a UserModel defined in your models.py
def wordopt(text):
        text = text.lower()
        text = re.sub('\[.*?\]', '', text)
        text = re.sub("\\W"," ",text) 
        text = re.sub('https?://\S+|www\.\S+', '', text)
        text = re.sub('<.*?>+', '', text)
        text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
        text = re.sub('\n', '', text)
        text = re.sub('\w*\d\w*', '', text)    
        return text
def user_url(request):
    if request.method == 'POST':
        u_url = request.POST.get('url')
        request.session['u_url'] = u_url  # Set the value in the session
        user_id = request.session['user_id']
        user = UserModel.objects.get(user_id=user_id)
        

        # Load vectorizer and model
        vectorizer = pickle.load(open('vectorizer.pkl', 'rb'))
        mnb = pickle.load(open('rfc_credit.pkl', 'rb'))
        a = wordopt(u_url)
        example_counts = vectorizer.transform([a])
        prediction = mnb.predict(example_counts)
        
        data_dict = {"url": u_url, 'Result': 'Safe URL' if prediction[0] == 'good' else 'Malicious URL'}

        # Redirect to the user_scan view

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data_dict)
        qr.make(fit=True)

        # Create an image from the QR code
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Save the image to BytesIO buffer
        image_buffer = BytesIO()
        qr_image.save(image_buffer)
        image_buffer.seek(0)

        # Save the QR code image to the media folder
        qr_code_path = f"media/user_{user_id}_qr.png"
        with open(qr_code_path, 'wb') as qr_file:
            qr_file.write(image_buffer.read())

        # Store the QR code path in the session
        request.session['qr_code_path'] = qr_code_path

        # Redirect to the user_scan view
        user_scan_url = reverse('user_scan')
        return redirect(user_scan_url + f'?qr_code_path={qr_code_path}')

    return render(request, 'user/user-url.html')
def user_scan(request):
    user_id = request.session['user_id']
    wo = WordNetLemmatizer()

    def wordopt(text):
        text = text.lower()
        text = re.sub('\[.*?\]', '', text)
        text = re.sub("\\W"," ",text) 
        text = re.sub('https?://\S+|www\.\S+', '', text)
        text = re.sub('<.*?>+', '', text)
        text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
        text = re.sub('\n', '', text)
        text = re.sub('\w*\d\w*', '', text)    
        return text
    # Load vectorizer and model
    vectorizer = pickle.load(open('vectorizer.pkl', 'rb'))
    mnb = pickle.load(open('rfc_credit.pkl', 'rb'))
    strr = request.session.get('u_url')
    print(strr, "urlllllll")

    a = wordopt(strr)
    example_counts = vectorizer.transform([a])
    prediction = mnb.predict(example_counts)
    print(prediction[0], "howwwww")
    result_message = ''
    if prediction[0] == 'good':
        result_message = 'Good'
    elif prediction[0] == 'bad':
        result_message = 'Bad'
  
    # Retrieve qr_code_path from the request's GET parameters
    qr_code_path = request.GET.get('qr_code_path', '')

    return render(request, 'user/user-scan.html', {'prediction': result_message, 'strr': strr, 'qr_code_path': qr_code_path})
