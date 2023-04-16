import shutil, sys, tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment
from ..forms import PostForm
# from ..views import POSTS_ON_PAGE


# PAGINATOR_ADDITIONAL_PAGES: int = 3
# POSTS_ON_PAGE_FOR_TEST: int = POSTS_ON_PAGE + PAGINATOR_ADDITIONAL_PAGES
# ONE_POST: int = 1
TEST_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x02\x00"
    b"\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x02\x00\x01\x00\x00\x02\x02\x0C"
    b"\x0A\x00\x3B"
)
IMG_NAME = 'test_gif.gif'
IMG_FOLDER = Post.image.field.upload_to
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormCreateEditTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group-slug',
            description='Тестовое описание',
        )

        # for x in range(POSTS_ON_PAGE_FOR_TEST):
        #     cls.post = Post.objects.create(
        #         text=f'Пост {x}',
        #         author=cls.user,
        #         group=cls.group
        #     )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """Создание поста и его добавления в БД"""
        uploaded_img = SimpleUploadedFile(
            name=IMG_NAME,
            content=TEST_GIF,
            content_type='image/gif',
        )

        post_content = {
            'text': 'Новый пост',
            'group': self.group.pk,
            'image': uploaded_img,
        }

        post_count_before = Post.objects.count()

        self.auth_client.post(
            reverse('posts:post_create'),
            data=post_content,
        )

        post_count_after = Post.objects.count()

        post = Post.objects.get(text=post_content['text'],)
        self.assertEqual(post_content['text'], post.text)
        self.assertEqual(post_content['group'], post.group.pk)
        self.assertEqual(post.image, IMG_FOLDER + IMG_NAME)
        #self.assertEqual(sys.getsizeof(post), IMG_FOLDER + IMG_NAME)

        # self.assertTrue(post_content.exists())

        # self.assertTrue(
        #     Post.objects.filter(
        #         text='Новый пост',
        #         group=self.group.pk,
        #         # image='posts/test_gif.gif',
        #         # IMG_FOLDER + uploaded_img.name,
        #     ).exists()
        # )

        self.assertNotEqual(
            post_count_before,
            post_count_after,
        )

    def test_post_edit(self):
        """Изменения поста и его изменение в БД"""
        post_before = {
            'text': 'Пост будет отредактирован',
            'group': self.group.pk
        }

        post_after = {
            'text': 'Пост отредактирован',
            'group': self.group.pk
        }

        self.auth_client.post(
            reverse('posts:post_create'),
            data=post_before,
        )

        post_created = Post.objects.all()[0]

        self.auth_client.get(
            f'/posts/{post_created.id}/edit/'
        )

        self.auth_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': post_created.id
                }
            ),
            data=post_after
        )

        post_edited = Post.objects.all()[0]

        self.assertNotEqual(post_created.text, post_edited.text)


    def test_add_comment_authorized(self):
        special_post = Post.objects.create(
            text='Пост для комментариев авторизованного пользователя.',
            author=self.user,
            group=self.group
        )

        comment_content = {
            'text': 'Комментарий авторизованного пользователя'
        }

        comment_count_before = Comment.objects.count()

        self.auth_client.post(
            reverse(
                'posts:add_comment', args=[special_post.id]
            ),
            comment_content
        )

        comment_count_after = Comment.objects.count()
        comment = Comment.objects.first()

        response = self.auth_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': special_post.id}
            )
        )

        self.assertEqual(
            comment_count_before + 1,
            comment_count_after
        )
        self.assertEqual(comment.text, comment_content['text'])
        self.assertEqual(
            comment.author.username,
            self.user.username
        )
        self.assertEqual(comment.post, special_post)
        self.assertEqual(response.context['comments'][0], comment)


    def test_add_comment_not_authorized(self):
        special_post = Post.objects.create(
            text='Пост для комментариев НЕ авторизованного пользователя.',
            author=self.user,
            group=self.group
        )

        comment_content = {
            'text': 'Комментарий НЕ авторизованного пользователя'
        }

        comment_count_before = Comment.objects.count()

        self.guest_client.post(
            reverse(
                'posts:add_comment', args=[special_post.id]
            ),
            comment_content
        )

        comment_count_after = Comment.objects.count()

        self.assertEqual(
            comment_count_before,
            comment_count_after
        )
