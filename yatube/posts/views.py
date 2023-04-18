from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow

POSTS_ON_PAGE: int = 10


def get_page(request, post_list, posts_on_page=POSTS_ON_PAGE):
    page = Paginator(post_list, posts_on_page)
    page_number = request.GET.get('page')
    return page.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = get_page(request, post_list, POSTS_ON_PAGE)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all().order_by('-pub_date')
    page_obj = get_page(request, post_list, POSTS_ON_PAGE)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all().order_by('-pub_date')
    page_obj = get_page(request, post_list, POSTS_ON_PAGE)
    following = (request.user != user
                 and request.user.is_authenticated
                 and Follow.objects.filter(user=request.user, author=user,
                                           ).exists()
                 )
    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    post_count = author.posts.all().count()
    form = CommentForm(request.POST or None)
    comments = Comment.objects.select_related('author').filter(post=post)
    context = {
        'post': post,
        'post_count': post_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    is_edit = False
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', post.author.username)

    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'is_edit': is_edit,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        pk=post_id
    )
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Подписки пользователя"""
    post_list = Post.objects.select_related(
        'author',
        'group',
    ).filter(author__following__user=request.user)

    page_obj = get_page(request, post_list, POSTS_ON_PAGE)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на автора"""
    user = get_object_or_404(User, username=username)

    if username != request.user.username:
        Follow.objects.get_or_create(user=request.user, author=user)

    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора"""
    get_object_or_404(
        Follow,
        author__username=username,
        user=request.user,
    ).delete()

    return redirect("posts:profile", username=username)
