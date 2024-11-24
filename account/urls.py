from django.contrib import admin
from django.urls import path,include
from .views import RegisterUserView,VerifyUserEmail,LoginUserView
urlpatterns = [
   
    path('register/',RegisterUserView.as_view(),name='register'),
    path('verify-email/',VerifyUserEmail.as_view(),name='verify'),
    path('login/',LoginUserView.as_view(),name='login'),

]
