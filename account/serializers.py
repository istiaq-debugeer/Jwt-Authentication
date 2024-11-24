from django.urls import reverse
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import smart_str,smart_bytes,force_str
from .utils import send_normal_email

class UserRegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(max_length=68,min_length=6,write_only=True)
    password2=serializers.CharField(max_length=68,min_length=6,write_only=True)

    class Meta:
        model=User
        fields=['email','first_name','last_name','password','password2']

    def validate(self,attrs):
        password=attrs.get('password','')
        password2=attrs.get('password2','')
        if password!=password2:
            raise serializers.ValidationError("password do not match")
        return attrs
    
    def create(self,validated_data):
        user=User.objects.create(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
           
                                
        )  
        user.set_password(validated_data['password'])
        user.save()

        return user
    

class LoginSerializer(serializers.ModelSerializer):
        email=serializers.EmailField(max_length=255,min_length=6)
        password=serializers.CharField(max_length=68,write_only=True)
        full_name=serializers.CharField(max_length=255,read_only=True)
        access_token=serializers.CharField(max_length=255,read_only=True)
        refresh_token=serializers.CharField(max_length=255,read_only=True)

        class Meta:
            model=User
            fields=['email','password','full_name','access_token','refresh_token']

        def validate(self,attrs):
            email=attrs.get('email')
            password=attrs.get('password')
            request=self.context.get('request')
            # user=User.objects.filter(email=email,password=password).first()
            user=authenticate(request,email=email,password=password)

            print(user)
            if not user:
                 raise AuthenticationFailed("invalide credential try again")
            if not user.is_verified:
                 raise AuthenticationFailed("Email is not verified")
            user_tokens=user.tokens()

            return {
                 'email':user.email,
                 'full_name':user.get_full_name,
                 'access_token':str(user_tokens.get('access')),
                 'refresh_token':str(user_tokens.get('refresh'))
            }                 
            # return super().validate(attrs)    

class PasswordResetSerializer(serializers.Serializer):
    email=serializers.EmailField(max_length=255)

    class Meta:
          fields=['email']

    def validate(self, attrs):
         email=attrs.get('email')
         if User.objects.filter(email=email).exists():
              user=User.objects.get(emial=email)
              uid64=urlsafe_base64_encode(smart_bytes(user.id))
              token=PasswordResetTokenGenerator().make_token(user)
              request=self.context.get('request')
              site_domain=get_current_site(request).domain
              relative_link=reverse('passowrd-reset-confirm',kwargs={'uid64':uid64,'token':token})
              abslink=f"http://{site_domain}{relative_link}"
              email_body=f'Hi use the link below to reset your password \n{abslink}'
              data={
                   'email_body':email_body,
                   'email_subject':"Reset your Password",
                   'to_email':user.email
              }
              send_normal_email(data)
         return super().validate(attrs)(self,attrs)


class SetNewPasswordSerializer(serializers.Serializer):
     password=serializers.CharField(max_length=100,min_length=6,write_only=True)
     confirm_password=serializers.CharField(max_length=100,min_length=6,write_only=True)
     uid64=serializers.CharField(write_only=True)
     token=serializers.CharField(write_only=True)

     class Meta:
          fields=["password","confirm_password",'uid64','token']

     def validate(self,attrs):
          try:
            token=attrs.get('token')
            uid64=attrs.get('uid64')
            password=attrs.get('password')
            confirm_password=attrs.get('confirm_password') 

            user_id=force_str(urlsafe_base64_decode(uid64))
            user=User.onjects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user,token):
                raise AuthenticationFailed("reset link is invalid or has expired",401)
            
            if password!=confirm_password:
                raise AuthenticationFailed("password does not match")
            user.set_password(password)
            user.save()
            return user
          except Exception as e:
               return  AuthenticationFailed(str(e))
        #   return super().validate(attrs)    