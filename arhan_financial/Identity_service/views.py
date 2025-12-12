from django.shortcuts import render, get_object_or_404, redirect
from .forms import *
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import *
from .tasks import *
#from .scripts.card_number_generator import generator

# Create your views here.


def index(request):
    return render(request, "index.html")

#ACCOUNT VIEWS

#Customer Registration View
def customer_register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            cd = user_form.cleaned_data
            
            # Check if email exists in username or email fields
            if user.objects.filter(models.Q(username=cd['email']) | models.Q(email=cd['email'])).exists():
                user_form.add_error('email', 'This email is already taken')
                return render(request, 'Identity_service/customer_register.html', {'user_form': user_form})
            
            try:
                new_user = user.objects.create_user(
                    first_name=cd['first_name'],
                    last_name=cd['last_name'],
                    username=cd['username'],
                    email=cd['username'],
                    password=cd['password'],
                    sex=cd['sex'],
                    date_of_birth=cd['date_of_birth'],
                    phone=cd['phone'],
                    is_customer=True,
                    is_active=True,
                )
                publish_customer_created.delay(new_user)
                return render(request, 'Identity_service/register_done.html', {'new_user': new_user})
            except Exception as e:
                user_form.add_error(None, f'Registration error: {str(e)}')
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'Identity_service/customer_register.html', {'user_form': user_form})


#IT Staff Registration View
def IT_register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            cd = user_form.cleaned_data
            
            # Check username existence (corrected)
            if user.objects.filter(username=cd['username']).exists():
                user_form.add_error('username', 'This username is already taken')
                return render(request, 'Identity_service/IT_register.html', {'user_form': user_form})
            
            try:
                new_user = user.objects.create_user(
                    first_name=cd['first_name'],
                    last_name=cd['last_name'],
                    username=cd['username'],
                    email=cd['email'],
                    password=cd['password'],
                    sex=cd['sex'],
                    date_of_birth=cd['date_of_birth'],
                    phone=cd['phone'],
                    is_IT=True,
                    is_active=True
                )
                #publish_staff_created.delay(new_user)
                return render(request, 'Identity_service/register_done.html', {'new_user': new_user})
            except Exception as e:
                user_form.add_error(None, f'Registration error: {str(e)}')
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'Identity_service/IT_register.html', {'user_form': user_form})


@login_required
def user_edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'user updated successfully')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
    return render(request, 'Identity_service/user_edit.html', {'user_form': user_form, 'section': 'edit'})



#CUSTOMER RELATED LOGIC
def customer_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
        if user is not None:
            if user.is_active and user.is_customer:
                login(request, user)
                #publish_user_loggedIn.delay(user)
                return render(request, 'Identity_service/dashboard_c.html')
            else:
                return HttpResponse('Disabled account')
        else:
            return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    return render(request, 'customer_login.html', {'form': form})  

def staff_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                #publish_user_loggedIn.delay(user)
                return render(request, 'dashboard.html')
            else:
                return HttpResponse('Disabled account')
        else:
            return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    return render(request, 'registration/customer_login.html', {'form': form})  


#IT RELATED LOGIC
def Staff_register(request):                    #Staff Registration View
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            cd = user_form.cleaned_data
            
            # Check username existence (corrected)
            if user.objects.filter(username=cd['username']).exists():
                user_form.add_error('username', 'This username is already taken')
                return render(request, 'Identity_service/staff_register.html', {'user_form': user_form})
            
            try:
                new_user = user.objects.create_user(
                    first_name=cd['first_name'],
                    last_name=cd['last_name'],
                    username=cd['username'],
                    email=cd['email'],
                    password=cd['password'],
                    sex=cd['sex'],
                    date_of_birth=cd['date_of_birth'],
                    phone=cd['phone'],
                    is_other_staff=cd.get('is_other_staff', True),
                    is_active=True
                )
                #publish_staff_created.delay(new_user)
                return render(request, 'Identity_service/register_done.html', {'new_user': new_user})
            except Exception as e:
                user_form.add_error(None, f'Registration error: {str(e)}')
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'Identity_register/staff_register.html', {'user_form': user_form})



        
    

