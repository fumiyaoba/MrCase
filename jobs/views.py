from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from jobs.forms import CaseForm
from jobs.models import Case

@login_required
def menu(request):
    return render(request,'menu.html')

@login_required
def case_create(request):
    if request.method == "POST":
        form = CaseForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect("case_list")
    else:
        form = CaseForm()
    return render(request, "cases/create.html", {"form": form})

@login_required
def case_list(request):
    cases = Case.objects.order_by("-created_at")
    return render(request, "cases/list.html", {"cases": cases})