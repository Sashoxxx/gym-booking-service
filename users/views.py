import logging
from base64 import urlsafe_b64encode

from django.contrib import messages
from django.contrib.auth import get_user_model

from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UserPassesTestMixin
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView
)

from users.forms import (
    UserSearchForm,
    CustomUserCreationForm,
    AddBalanceForm,
    StaffUserCreationForm,
    UserUpdateForm,
)
from users.models import Account
from users.services.token_service import account_activation_token

User = get_user_model()

logger = logging.getLogger(__name__)

class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    permission_required = "users.view_user"
    raise_exception = True

    def get_queryset(self):
        queryset = User.objects.select_related("account").all()
        self.form = UserSearchForm(self.request.GET or None)
        if self.form.is_valid():
            search = self.form.cleaned_data.get("search")
            role = self.form.cleaned_data.get("role")
            if search:
                queryset = queryset.filter(
                    Q(username__icontains=search) |
                    Q(email__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search)
                )
            if role:
                queryset = queryset.filter(role=role)
        return queryset.order_by("username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context

class UserDetailView(DetailView):

    model = User
    template_name = "users/user_detail.html"
    context_object_name = "profile_user"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("account")
        )

    def get_object(self, queryset=None):
        queryset = self.model.objects.select_related('account')
        return super().get_object(queryset=queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        context.update({

            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "role": user.get_role_display(),
            "account_balance": getattr(user.account, "balance", 0),
        })

        if user.role == User.Roles.CLIENT:
            context["recent_bookings"] = (
                user.bookings
                .select_related("session__gym")
                .order_by("-created_at")[:5]
            )

        elif user.role == User.Roles.TRAINER:
            context["recent_sessions"] = (
                user.trainer_sessions
                .select_related("gym")
                .order_by("-start_time")[:5]
            )

        return context

class StaffUserCreateView(UserPassesTestMixin, CreateView):
    model = User
    form_class = StaffUserCreationForm
    template_name = "registration/create_staff.html"
    success_url = reverse_lazy("users:user-list")

    def test_func(self):
        return self.request.user.is_superuser


class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")


    def form_valid(self, form):
        try:
            with transaction.atomic():
                form.instance.role = User.Roles.CLIENT
                form.instance.is_active = False
                user = form.save()

                mail_subject = "Activate your account"
                uid = urlsafe_b64encode(force_bytes(user.id)).decode()
                token = account_activation_token.make_token(user)
                scheme = self.request.scheme
                domain = get_current_site(self.request).domain
                url = f"{scheme}://{domain}/users/activate/{uid}/{token}/"


                html_content = render_to_string(
                    "registration/emails/acc_active_email.html",
                    {
                        "url": url,
                        "user": user
                    }
                )

                email = EmailMessage(
                    mail_subject,
                    html_content,
                    to=[user.email]
                )
                email.content_subtype = "html"

                email.send()
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return super().form_valid(form)

        return render(self.request, "registration/email_confirmation_sent.html")


class ActivateAccountView(View):
    def get(self, request: HttpRequest, uid: str, token: str):
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None:
            if user.is_active:
                messages.info(request, "Your account is already activated.")
                return redirect("login")

            if account_activation_token.check_token(user, token):
                user.is_active = True
                user.save()

                messages.success(
                    request,
                    "Thank you for confirming your email. You can now login to your account.",
                )
                return redirect("login")

        return render(request, "registration/activation_invalid.html")

class UserUpdateView(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "users/user_update.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            "users:user-detail", kwargs={"pk": self.request.user.pk}
        )


class UserDeleteView(DeleteView):
    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy("login")

    def get_object(self, queryset=None):
        return self.request.user


class AddBalanceView(LoginRequiredMixin, FormView):
    template_name = "users/add_balance.html"
    form_class = AddBalanceForm

    def get_success_url(self):
        return reverse_lazy(
            "users:user-detail", kwargs={"pk": self.request.user.pk}
        )

    def form_valid(self, form):
        amount = form.cleaned_data["amount"]

        with transaction.atomic():
            account = getattr(self.request.user, "account", None)
            if account is None:
                account = Account.objects.create(
                    user=self.request.user, balance=0
                )

            account.add_money(amount)

        return super().form_valid(form)
