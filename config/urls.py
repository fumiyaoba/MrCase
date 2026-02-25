from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from jobs import views as jobs_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # 認証
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # メニュー
    path("", jobs_views.menu, name="menu"),

    # 案件
    path("cases/", jobs_views.case_list, name="case_list"),
    path("cases/new/", jobs_views.case_create, name="case_create"),
    path("cases/<int:pk>/edit/", jobs_views.case_edit, name="case_edit"),
    path("cases/<int:pk>/delete/", jobs_views.case_delete, name="case_delete"),

    # 工数
    path("manhours/", jobs_views.manhour_list, name="manhour_list"),
    path("manhours/download/", jobs_views.manhour_download, name="manhour_download"),
]
