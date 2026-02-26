"""
jobs/views.py
"""
import io
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl import Workbook

from jobs.forms import CaseForm, UserCreateForm, UserEditForm
from jobs.models import Case, ManHourRecord


# ------------------------------------------------------------------ #
# ヘルパー
# ------------------------------------------------------------------ #

def is_admin(user):
    return user.is_staff or user.is_superuser


def admin_required(view_func):
    return login_required(user_passes_test(is_admin, login_url="/")(view_func))


# ------------------------------------------------------------------ #
# メニュー
# ------------------------------------------------------------------ #

@login_required
def menu(request):
    return render(request, "menu.html")


# ------------------------------------------------------------------ #
# 案件
# ------------------------------------------------------------------ #

@login_required
def case_list(request):
    cases = Case.objects.order_by("-created_at")
    return render(request, "cases/list.html", {"cases": cases})


@admin_required
def case_create(request):
    if request.method == "POST":
        form = CaseForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f"案件「{obj.name}」を登録しました。")
            return redirect("case_list")
    else:
        form = CaseForm()
    return render(request, "cases/create.html", {"form": form})


@admin_required
def case_edit(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == "POST":
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, f"案件「{case.name}」を更新しました。")
            return redirect("case_list")
    else:
        form = CaseForm(instance=case)
    return render(request, "cases/edit.html", {"form": form, "case": case})


@admin_required
def case_delete(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == "POST":
        name = case.name
        case.delete()
        messages.success(request, f"案件「{name}」を削除しました。")
        return redirect("case_list")
    return render(request, "cases/delete_confirm.html", {"case": case})


# ------------------------------------------------------------------ #
# 工数
# ------------------------------------------------------------------ #

@login_required
def manhour_list(request):
    year = request.GET.get("year", date.today().year)
    month = request.GET.get("month", date.today().month)
    case_id = request.GET.get("case_id", "")

    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = date.today().year
        month = date.today().month

    records = ManHourRecord.objects.filter(
        work_date__year=year,
        work_date__month=month,
    )

    if not is_admin(request.user):
        records = records.filter(assignee=request.user.get_full_name() or request.user.username)

    if case_id:
        try:
            records = records.filter(case_id=int(case_id))
        except (ValueError, TypeError):
            pass

    records = records.order_by("work_date", "assignee")

    months = range(1, 13)
    years = range(2020, date.today().year + 1)
    cases = Case.objects.filter(is_active=True).order_by("name")

    context = {
        "records": records,
        "year": year,
        "month": month,
        "months": months,
        "years": years,
        "cases": cases,
        "selected_case_id": case_id,
        "total_hours": sum(r.hours for r in records),
    }
    return render(request, "manhours/list.html", context)


@login_required
def manhour_download(request):
    year = int(request.GET.get("year", date.today().year))
    month = int(request.GET.get("month", date.today().month))

    records = ManHourRecord.objects.filter(
        work_date__year=year,
        work_date__month=month,
    )

    if not is_admin(request.user):
        records = records.filter(assignee=request.user.get_full_name() or request.user.username)

    records = records.order_by("work_date", "assignee")

    wb = Workbook()
    ws = wb.active
    ws.title = "raw"

    ws.append(["日付", "案件名", "担当者", "時間(h)"])
    for r in records:
        ws.append([r.work_date.isoformat(), r.project_name, r.assignee, float(r.hours)])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"manhour_{year}{month:02d}.xlsx"
    response = HttpResponse(
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ------------------------------------------------------------------ #
# ユーザー管理
# ------------------------------------------------------------------ #

@admin_required
def user_list(request):
    users = User.objects.order_by("username")
    return render(request, "users/list.html", {"users": users})


@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"ユーザー「{user.username}」を作成しました。")
            return redirect("user_list")
    else:
        form = UserCreateForm()
    return render(request, "users/create.html", {"form": form})


@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"ユーザー「{user.username}」を更新しました。")
            return redirect("user_list")
    else:
        form = UserEditForm(instance=user)
    return render(request, "users/edit.html", {"form": form, "target_user": user})


@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    # 自分自身は削除できない
    if user == request.user:
        messages.error(request, "自分自身は削除できません。")
        return redirect("user_list")
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"ユーザー「{username}」を削除しました。")
        return redirect("user_list")
    return render(request, "users/delete_confirm.html", {"target_user": user})
