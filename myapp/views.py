from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import *
from django.core.mail import EmailMessage
from django.conf import settings

from django.template.loader import render_to_string
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from .forms import OrderForm,createUserForm,CustomerForm
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from .filters import orderFilter
from .decorators import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
# Create your views here.

@unauthenticated_user
def registerPage(request):
        form =createUserForm()
        if request.method == 'POST':
            form =createUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                username = form.cleaned_data.get('username')
               
                messages.success(request,'account was created for '+ username)
                
                template = render_to_string('myapp/email_template.html',{'name':request.user.username})
                email = EmailMessage(
                    'Thanks for registering',
                    template,
                    settings.EMAIL_HOST_USER,
                    [request.user.email]
                )
                email.fail_silently = False
                email.send()
                return redirect('login')
                
                
        context = {'form':form}
        return render(request,'myapp/register.html',context)

@unauthenticated_user
def loginPage(request):
   
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request,username=username,password=password)
            if user is not None:
                login(request,user)
                return redirect('home')
            else:
                messages.info(request,'Username or Password is incorrect')
                return redirect('login')
        context = {}
        return render(request,'myapp/login.html',context)
def logoutUser(request):
    logout(request)
    
    return redirect('login')


@login_required(login_url='login')
@admin_only
def home(request):
    orders = Order.objects.all()
    customers = Customer.objects.all()
    
    total_customers = customers.count()
    
    total_orders = orders.count()
    delivered = orders.filter(status = 'Delivered').count()
    pending = orders.filter(status = 'Pending').count()
    
    context = {'orders':orders,'customers':customers,'total_orders':total_orders,
               'delivered':delivered,'pending':pending
               }
    return render(request,'myapp/dashboard.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def userPage(request):
    orders = request.user.customer.order_set.all()
    print(orders)
    
    total_orders = orders.count()
    delivered = orders.filter(status = 'Delivered').count()
    pending = orders.filter(status = 'Pending').count()
    context = {'orders':orders,'total_orders':total_orders,
               'delivered':delivered,'pending':pending}
    return render(request,'myapp/user.html',context)

def accountSettings(request):
    customer = request.user.customer
    form = CustomerForm(instance=customer)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST,request.FILES,instance=customer)
        if form.is_valid():
            form.save()
            return redirect('account')
        
    context ={'form':form}
    return render(request,'myapp/account_settings.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def products(request):
    products = Product.objects.all()
    context = {'products':products}
    
    return render(request,'myapp/products.html',context)

@login_required(login_url='login') 
@allowed_users(allowed_roles=['admin'])
def customer(request,pk):
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    order_count = orders.count()
    myFilter = orderFilter(request.GET,queryset=orders)
    orders = myFilter.qs
    
    myFilter = orderFilter(request.GET,queryset=orders)
    orders = myFilter.qs
    context = {'customer':customer,'orders':orders,'order_count':order_count,'myFilter':myFilter}
    return render(request,'myapp/customer.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def createOrder(request,pk):
    orderFormSet = inlineformset_factory(Customer,Order,fields=('product','status'),extra=10)
    customer = Customer.objects.get(id=pk)
    formset = orderFormSet(queryset=Order.objects.none(),instance=customer)
    #form = OrderForm(initial={'customer':customer})
    if request.method == 'POST':
        #print(request.POST)
        #form =OrderForm(request.POST)
        formset = orderFormSet(request.POST,instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('home')
    context = {'formset':formset}
    return render(request,'myapp/order_form.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def updateOrder(request,pk):
    orders = Order.objects.get(id=pk)
    form = OrderForm(instance=orders)
    if request.method == 'POST':
        #print(request.POST)
        form =OrderForm(request.POST,instance=orders)
        if form.is_valid():
            form.save()
            return redirect('home')
    
    context = {'form':form}
    return render(request,'myapp/order_form.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def deleteOrder(request,pk):
    orders = Order.objects.get(id=pk)
   
    if request.method == 'POST':
        orders.delete()
        return redirect('home')
    
    context = {'item':orders}
    return render(request,'myapp/delete.html',context)
    