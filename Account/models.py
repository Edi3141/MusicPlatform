from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from django.dispatch import receiver
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail


class MyUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **kwargs):
        if not email:
            return ValueError('Указанный адрес электронной почты должен быть установлен!')
        email = self.normalize_email(email=email)
        user = self.model(email=email, **kwargs)
        user.create_activation_code()
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        return self._create_user(email, password, **kwargs)

    def create_superuser(self, email, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)
        if kwargs.get('is_staff') is not True:
            raise ValueError('Статус суперпользователя должен быть is_staff=True!')
        if kwargs.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь статус is_superuser=True!')
        return self._create_user(email, password, **kwargs)


class MyUser(AbstractUser):
    email = models.EmailField('email address', unique=True)
    password = models.CharField(max_length=100)
    activation_code = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', blank=True, default='avatars/default_avatar.jpg')
    is_active = models.BooleanField(_('active'), default=False,
                                    help_text=_("Указывает, следует ли считать этого пользователя активным."
                                                "Отменить выбор вместо удаления учетных записей."))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = MyUserManager()

    def __str__(self):
        return self.email

    def create_activation_code(self):
        import uuid
        code = str(uuid.uuid4())
        self.activation_code = code


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    email_plaintext_message = "{}?token={}".format(reverse('password_reset:reset-password-request'),
                                                   reset_password_token.key)

    send_mail(
        # title:
        "Password Reset for {title}".format(title="Some website title"),
        # message:
        email_plaintext_message,
        # from:
        "noreply@somehost.local",
        # to:
        [reset_password_token.user.email]
    )
