from .models import Post
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from .models import Post, User, UserProfile, Comment
from .forms import PostForm, CommentForm, UserProfileForm
from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required(login_url='/accounts/login')
def index(request):
    current_user = request.user
    current_profile = UserProfile.objects.filter(user = request.user)  
    posts = Post.objects.all()[::-1]
    comments = Comment.objects.all()

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.profile = current_user
            post.user_profile = current_profile

            post.save()
            post_form = PostForm()
            return redirect('index')
    else:
        post_form = PostForm

    return render(request, "index.html", {"posts": posts, "current_user": current_user, "post_form": post_form, "comments": comments, })


def post(request,id):
    post = Post.objects.get(id=id)     
    comments = Comment.objects.filter(post__id=id)
    current_user = request.user
    current_profile = UserProfile.objects.filter(user = request.user)  

    if request.method == "POST":
        comment_form = CommentForm(request.post)

        if comment_form.is_valid:
            comment = comment_form.save(commit=False)
            comment.user = current_user
            comment.post=post
            comment.save()
            comment_form = CommentForm()
            return redirect('post,post.id')
    else:
        comment_form = CommentForm()

    return render(request, "post.html",{"post":post,"current_user":current_user,"current_profile":current_profile,"comment_form":comment_form,"comments":comments,})


def like(request,id):
    post=Post.objects.get(pk = id)
    post.likes += 1
    post.save()
    return redirect('index')



@login_required
def search(request):
    
    if request.method == "GET":
        search_term = request.GET.get("search")
        searched_user = User.objects.get(username = search_term)
        try:
            searched_profile = UserProfile.objects.get(id = searched_user.id)
            posts = Post.objects.filter(profile__id=searched_user.id)[::-1]
            message = "{}".format(search_term)
        except DoesNotExist:
            return HttpResponseRedirect(reverse("index")) 
        
        return render(request, "search_results.html", context={"message":message,
                                                                        "users":searched_user,
                                                                        "profiles":searched_profile,
                                                                        "posts":posts})
    else:
        message = "You have not searched for any photo"
        return render(request, "instagrm/search.html", context={"message":message})



@login_required
def profile(request, id):

    user = User.objects.get(id=id)
    profile = UserProfile.objects.filter(user = request.user) 
    posts = Post.objects.filter(profile__id=id)[::-1]
    p_form= UserProfileForm()
    return render(request, "profile.html", context={"user":user,
                                                             "profile":profile,
                                                             "posts":posts,"p_form":p_form})
