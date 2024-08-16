from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string

def validate_no_integers(value):
    if any(char.isdigit() for char in value):
        raise ValidationError('The value cannot contain numbers.')

# Create your models here.

class MyAccountManager(BaseUserManager):

    def create_user(self, first_name, last_name,username, email, password=None):
        if not email:
            raise ValueError('User must have an email address')
        
        if not username:
            raise ValueError('User must have a username')   # To covert capital letter into small letter
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
        )

        user.set_password(password)
        user.save(using = self._db)
        return user
    

    def create_superuser(self, first_name, last_name, username, email, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            password = password,
        )

        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using = self._db)
        return user




class Account(AbstractBaseUser):
    first_name    = models.CharField(max_length=50, validators=[validate_no_integers])
    last_name    = models.CharField(max_length=50, validators=[validate_no_integers])
    username      = models.CharField(max_length=50, unique=True)
    email         = models.EmailField(max_length=100, unique=True)
    phone_number  = models.CharField(max_length=50)
    referral_code = models.CharField(max_length=10,blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    # required
    date_joined   = models.DateTimeField(auto_now_add=True)
    last_login    = models.DateTimeField(auto_now_add=True)
    is_admin      = models.BooleanField(default=False)
    is_staff      = models.BooleanField(default=False)
    is_active     = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)


    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def full_name(self):
        return f'{self.first_name} {self.last_name}'
        

    objects = MyAccountManager()

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, add_label):
        return True
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = get_random_string(10).upper()
        super(Account, self).save(*args, **kwargs)


class OTP(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at
    

class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address_line_1  = models.CharField(max_length=100, blank=True)
    address_line_2  = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(blank=True, upload_to='userprofile')
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.user.first_name
    
    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'
    

class UserAddress(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    first_name    = models.CharField(max_length=50, validators=[validate_no_integers])
    last_name    = models.CharField(max_length=50, validators=[validate_no_integers])
    email         = models.EmailField(max_length=100, null=True, blank=True)
    phone_number  = models.CharField(max_length=50)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def full_address(self):
        return f'{self.first_name} {self.last_name}, {self.email}, {self.phone_number},{self.address_line_1} {self.address_line_2}, {self.city}, {self.state}, {self.country}'.strip()

    def __str__(self):
        return f'{self.address_line_1}, {self.city}'