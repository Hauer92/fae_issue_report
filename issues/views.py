from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone 
from django.db.utils import DatabaseError
from datetime import timedelta, datetime


# Assuming forms.py is in the same app directory
from .models import Issue, Comment
from .forms import IssueForm , CommentForm

from django.contrib.auth.decorators import login_required # 確保只有登入者可以留言

# 處理新增問題的 View
def create(request):
    """
    處理新增問題頁面或表單提交。
    """
    if request.method == 'POST':
        # Pass the POST data to the form
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            
            # Ensure the user is authenticated before setting created_by
            if not request.user.is_authenticated:
                # Handle unauthenticated user attempt to create
                return HttpResponseForbidden("您必須登入才能建立問題 (You must be logged in to create an issue).")

            # Set the mandatory field created_by automatically
            issue.created_by = request.user 
            issue.save()
            
            # TODO: Replace with the actual detail view name when implemented
            return redirect('issues:home') 
        
        # If form is invalid, fall through to render with errors
    else:
        # On GET request, instantiate an empty form
        form = IssueForm()
    
    # CRITICAL FIX: The template path must include the app name ('issues/create.html') 
    # to correctly resolve the file located at fae_issue_report/issues/templates/issues/create.html.
    return render(request, 'issues/create.html', { 
        'form': form,
        'title': '建立新問題 (Create New Issue)'
    })


# 處理單個問題詳細頁面的 View
@login_required # 通常留言需要登入
def detail(request, pk):
    """
    處理單個問題的詳細視圖。
    """
    # 查找問題，找不到則返回 404
    issue = get_object_or_404(Issue, pk=pk) 

    # 獲取所有留言
    comments = issue.comments.all()

    if request.method == 'POST':
        # 處理留言提交
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.issue = issue
            new_comment.user = request.user # 將留言者設定為當前登入使用者
            new_comment.save()
            
            # 重定向回當前頁面以清除 POST 數據，防止重複提交
            return redirect('issues:detail', pk=issue.pk)
    else:
        # 顯示空表單
        comment_form = CommentForm()

    context = {
        'issue': issue,
        'comments': comments,      # 傳遞所有留言
        'comment_form': comment_form, # 傳遞留言表單
    }
    
    # 渲染 detail.html 模板
    return render(request, 'issues/detail.html', {'issue': issue}, context)


def home(request):
    """
    處理首頁，顯示問題列表並應用篩選器。
    """
    # [Content of your home view remains the same]
    recent_issues = []
    recent_count = 0
    issue_status_choices = []
    
    try:
        # NOTE: Using Issue.Status.choices if Issue.STATUS_CHOICES is deprecated/not working
        issue_status_choices = Issue.Status.choices 
        queryset = Issue.objects.all().select_related('assigned_to', 'created_by')
        recent_issues = queryset.order_by('-created_at')[:10]
        recent_count = queryset.count()
    
    except DatabaseError as e:
        print(f"Database Error in home view: {e}")
        
    now = timezone.now()

    for issue in recent_issues:
        if hasattr(issue, 'sla_due_at') and issue.sla_due_at:
            if issue.sla_due_at.tzinfo is None or issue.sla_due_at.tzinfo.utcoffset(issue.sla_due_at) is None:
                issue_sla_due_at = timezone.make_aware(issue.sla_due_at, timezone.get_current_timezone())
            else:
                issue_sla_due_at = issue.sla_due_at

            time_diff = issue_sla_due_at - now
            
            if time_diff < timedelta(0):
                days_overdue = abs(time_diff.days)
                issue.due_label = f"{days_overdue}天" if days_overdue >= 1 else "已過期"
                issue.due_style = 'danger'
            elif time_diff < timedelta(days=1):
                seconds = time_diff.total_seconds()
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                issue.due_label = f"{hours}時{minutes}分"
                issue.due_style = 'warning'
            else:
                issue.due_label = f"{time_diff.days}天"
                issue.due_style = 'success'
        else:
            issue.due_label = "N/A"
            issue.due_style = 'default'

    context = {
        'recent_issues': recent_issues,
        'recent_count': recent_count,
        'issue_status_choices': issue_status_choices,
        'current_filter': request.GET.get('status', 'all'),
    }
    
    return render(request, 'issues/home.html', context)
