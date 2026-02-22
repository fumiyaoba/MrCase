from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from jobs.views import menu
from jobs import views as jobs_views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", menu, name="menu"),
    # ログイン/ログアウト
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cases/", jobs_views.case_list, name="case_list"),
    path("cases/new/", jobs_views.case_create, name="case_create"),
]