from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Profile, Photo, Post
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import uuid
import boto3
import os

# Create your views here.
def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

def signup(request):
  error_message = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('create_profile')
    else:
      error_message = 'Invalid sign up - try again'
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)


class create_profile(LoginRequiredMixin, CreateView):
  model = Profile
  fields = ['username', 'name', 'avatar', 'age', 'bio']
  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)


@login_required
def add_photo(request, post_id):
    # photo-file will be the "name" attribute on the <input type="file">
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # just in case something goes wrong
        try:
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            # build the full url string
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
            # we can assign to cat_id or cat (if you have a cat object)
            Photo.objects.create(url=url, post_id=post_id)
        except Exception as e:
            print('An error occurred uploading file to S3')
            print(e)
    return redirect('post_detail', post_id=post_id)

def post_index(request):
  posts = Post.objects.all()
  return render(request, 'post/index.html', { 'posts' : posts })

def post_detail(request, post_id):
  post = Post.objects.get(id=post_id)
  return render(request, 'post/detail.html', {'post': post})

class PostCreate(CreateView):
  model = Post
  fields = ['caption']
  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

class PostUpdate(UpdateView):
  model = Post
  fields = ['caption']

class PostDelete(DeleteView):
  model = Post
  success_url = '/posts/'