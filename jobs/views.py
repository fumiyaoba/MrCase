"""
jobs/views.py
"""
import io
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl import Workbook

from jobs.forms import CaseForm
from jobs.models import Case, ManHourRecord


# ------------------------------------------------------------------ #
# ヘルパー
# ------------------------------------------------------------------ #

def is_admin(user):
    return user.is_staff or user.is_superuser


def admin_required(view_func):
    """管理者のみアクセス可能なデコレーター"""
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
    # 絞り込みパラメータ
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

    # 使用者は自分の担当者名と一致するものだけ（管理者は全件）
    if not is_admin(request.user):
        records = records.filter(assignee=request.user.get_full_name() or request.user.username)

    # 案件絞り込み
    if case_id:
        try:
            records = records.filter(case_id=int(case_id))
        except (ValueError, TypeError):
            pass

    records = records.order_by("work_date", "assignee")

    # 月選択用リスト
    months = range(1, 13)

    # 年選択用リスト（2020年〜今年）
    years = range(2020, date.today().year + 1)

    # 案件選択用リスト（有効案件のみ）
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
    """当月（またはパラメータ指定）の工数を Excel でダウンロード"""
    year = int(request.GET.get("year", date.today().year))
    month = int(request.GET.get("month", date.today().month))

    records = ManHourRecord.objects.filter(
        work_date__year=year,
        work_date__month=month,
    )

    if not is_admin(request.user):
        records = records.filter(assignee=request.user.get_full_name() or request.user.username)

    records = records.order_by("work_date", "assignee")

    # Excel 生成
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
