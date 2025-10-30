from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Issue
from .forms import IssueForm

def home(request):
    qs = Issue.objects.all()

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    prio = request.GET.get('priority')
    if prio not in (None, ''):
        qs = qs.filter(priority=prio)

    recent_issues = qs.order_by('-updated_at', '-id')[:50]
    context = {
        'recent_issues': recent_issues,
        'recent_count': qs.count(),
    }
    return TemplateResponse(request, 'issues/home.html', context)

def detail(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    return TemplateResponse(request, 'issues/issue_detail.html', {'issue': issue})

@login_required
def create(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.created_by = request.user
            issue.save()
            messages.success(request, f'Issue #{issue.id} created.')
            return redirect('issues:detail', pk=issue.pk)
    else:
        form = IssueForm(initial={
            'status': Issue.Status.NEW,
            'priority': Issue.Priority.P2,
        })
    return TemplateResponse(request, 'issues/create.html', {'form': form})
