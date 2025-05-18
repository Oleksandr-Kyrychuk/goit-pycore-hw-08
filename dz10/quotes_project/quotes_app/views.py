import os
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'scrapy_integration.settings')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib import messages
from .models import Quote, Author, Tag
from .forms import RegisterForm, AuthorForm, QuoteForm
import subprocess
import logging

logger = logging.getLogger(__name__)

def index(request):
    quotes = Quote.objects.all().order_by('id')
    paginator = Paginator(quotes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    top_tags = Tag.objects.annotate(num_quotes=Count('quotes')).order_by('-num_quotes')[:10]
    return render(request, 'index.html', {'page_obj': page_obj, 'top_tags': top_tags})

def author_detail(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    quotes = Quote.objects.filter(author=author)
    return render(request, 'author_detail.html', {'author': author, 'quotes': quotes})

@login_required
def add_author(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Author added successfully.')
            return redirect('index')
    else:
        form = AuthorForm()
    return render(request, 'add_author.html', {'form': form})

@login_required
def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.created_by = request.user
            quote.save()
            for tag_name in form.cleaned_data['tags']:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                tag.quotes.add(quote)
            messages.success(request, 'Quote added successfully.')
            return redirect('index')
    else:
        form = QuoteForm()
    return render(request, 'add_quote.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registered successfully.')
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('index')

def tag_quotes(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    quotes = Quote.objects.filter(id__in=tag.quotes.all())
    top_tags = Tag.objects.annotate(num_quotes=Count('quotes')).order_by('-num_quotes')[:10]
    return render(request, 'tag_quotes.html', {'tag': tag, 'quotes': quotes, 'top_tags': top_tags})

@login_required
def scrape_quotes(request):
    if request.method == 'POST':
        logger.info("Received POST request for scraping")
        try:
            project_dir = 'D:\\goit-pycore-hw-08\\dz10\\quotes_project'
            env = os.environ.copy()
            env['PYTHONPATH'] = project_dir + (os.pathsep + env.get('PYTHONPATH', '') if 'PYTHONPATH' in env else '')
            env['DJANGO_SETTINGS_MODULE'] = 'quotes_project.settings'

            result = subprocess.run(
                ['scrapy', 'crawl', 'quotes'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            logger.info("Scrapy output: %s", result.stdout)
            logger.info("Scrapy errors: %s", result.stderr)
            if result.returncode == 0 and "spider_exceptions" not in result.stderr:
                logger.info("Scraping result: True")
                messages.success(request, 'Scraping completed successfully.')
            else:
                logger.error("Scraping failed with code %s: %s", result.returncode, result.stderr)
                messages.error(request, 'Scraping failed: Check server logs for details.')
        except subprocess.TimeoutExpired:
            logger.error("Scraping timed out after 60 seconds")
            messages.error(request, 'Scraping timed out after 60 seconds')
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            messages.error(request, f'Scraping failed: {str(e)}')
        logger.info("Redirecting to index")
        return redirect('index')
    logger.info("Rendering scrape page")
    return render(request, 'scrape.html')