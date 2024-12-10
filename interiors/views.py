import re
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from PIL import Image
import io
import time
import os
import requests
from django.core.mail import send_mail

@login_required(login_url='login')
def home(request):
    return render(request, 'index.html')


@login_required(login_url='login')
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Construct the subject and message content
        subject = f"Contact Form Submission from {name}"
        full_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

        try:
            # Send the email
            send_mail(
                subject,                          # Subject
                full_message,                     # Message
                settings.EMAIL_HOST_USER,         # From email
                ['Interiorsvisonary@gmail.com'],  # Recipient list
                fail_silently=False,
            )
            messages.success(
                request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, f"Failed to send message: {str(e)}")

        # Redirect to the same page or another page after submission
        return redirect('contact')

    return render(request, 'contact.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            # messages.success(request, 'You are now logged in.')
            # Replace 'home' with the name of your homepage view
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST.get('password2')  # Confirm password field
        phone_number = request.POST.get('phone_number')  # Phone number field

        if len(username) < 6:
            messages.error(
                request, "Username must be at least 6 characters long")
            return redirect('signup')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, "Invalid email address")
            return redirect('signup')

        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_pattern, password1):
            messages.error(
                request, "Password must be at least 8 characters long, include numbers, special characters, one uppercase letter, and one lowercase letter.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken")
            return redirect('signup')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('signup')
        user = User.objects.create_user(
            username=username, email=email, password=password1)
        user.save()
        messages.success(request, "User added Successfully")
        return redirect('signup')

    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def generate_image(request):
    if request.method == 'POST':
        # Validate required fields
        prompt = request.POST.get('prompt')
        if not prompt:
            messages.error(request, "Prompt is required.")
            return redirect('generate_image')

        try:
            strength = float(request.POST.get('strength', 0.75))
            if not (0.0 <= strength <= 1.0):
                messages.error(
                    request, "Strength must be a value between 0.0 and 1.0.")
                return redirect('generate_image')
        except ValueError:
            messages.error(request, "Invalid strength value provided.")
            return redirect('generate_image')

        # Validate file upload
        input_image = request.FILES.get('input_image')
        if not input_image:
            messages.error(request, "Input image is required.")
            return redirect('generate_image')

        # Save the input image to MEDIA_ROOT/uploads
        try:
            input_image_path = os.path.join(
                settings.MEDIA_ROOT, 'uploads', input_image.name)
            os.makedirs(os.path.dirname(input_image_path), exist_ok=True)
            with open(input_image_path, 'wb+') as f:
                for chunk in input_image.chunks():
                    f.write(chunk)
        except Exception as e:
            messages.error(
                request, f"Failed to save the input image: {str(e)}")
            return redirect('generate_image')

        # Set up request parameters for Stability API
        headers = {
            "Accept": "image/*",
            "Authorization": f"Bearer {settings.STABILITY_API_KEY}"
        }
        files = {'image': open(input_image_path, 'rb')}
        params = {
            "prompt": prompt,
            "strength": strength,
            "mode": "image-to-image",
            "model": "sd3.5-large-turbo"
        }

        # Send the request to the Stability API
        try:
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/control/structure",
                headers=headers,
                files=files,
                data=params
            )
        except requests.RequestException as e:
            messages.error(request, f"API request failed: {str(e)}")
            return redirect('generate_image')

        # Handle the API response
        if response.status_code == 200:
            try:
                # Save the generated image to MEDIA_ROOT/generated
                generated_filename = f"generated_{int(time.time())}.jpeg"
                output_image_path = os.path.join(
                    settings.MEDIA_ROOT, 'generated', generated_filename)
                os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
                with open(output_image_path, "wb") as f:
                    f.write(response.content)

                # Generate relative paths for displaying in template
                input_image_url = f"{settings.MEDIA_URL}uploads/{input_image.name}"
                generated_image_url = f"{settings.MEDIA_URL}generated/{generated_filename}"

                # Success message and render result
                messages.success(request, "Image generated successfully!")
                return render(request, 'result.html', {
                    'input_image_url': input_image_url,
                    'generated_image_url': generated_image_url,
                })
            except Exception as e:
                messages.error(
                    request, f"Failed to save the generated image: {str(e)}")
                return redirect('generate_image')
        else:
            # Handle API error response
            error_message = response.text or "An error occurred while generating the image."
            messages.error(request, f"API returned an error: {error_message}")
            return redirect('generate_image')

    # Render the form for GET requests
    return render(request, 'generate_image.html')
