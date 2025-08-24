from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UserPassesTestMixin
)
from django.db.models import Q
from django.urls import reverse_lazy
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
    CustomUserUpdateForm,
    AddBalanceForm,
    StaffUserCreationForm,
)
from users.models import Account

User = get_user_model()

class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context["username"] = user.username
        context["email"] = user.email
        context["first_name"] = user.first_name
        context["last_name"] = user.last_name
        context["phone_number"] = user.phone_number
        context["role"] = user.get_role_display()
        context["account_balance"] = getattr(user.account, "balance", 0)

        if user.role == User.Roles.CLIENT:
            context["recent_bookings"] = (
                user.bookings
                .select_related("session", "session__gym")
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

class UserUpdateView(UpdateView):
    model = User
    form_class = CustomUserUpdateForm
    template_name = "users/user_update.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user


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

        account = getattr(self.request.user, "account", None)
        if account is None:
            account = Account.objects.create(user=self.request.user, balance=0)

        account.add_money(amount)

        return super().form_valid(form)
