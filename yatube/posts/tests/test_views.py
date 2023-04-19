import shutil
import tempfile
from typing import List

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Follow
from ..views import POSTS_ON_PAGE


PAGINATOR_ADDITIONAL_PAGES: int = 3
POSTS_ON_PAGE_FOR_TEST: int = POSTS_ON_PAGE + PAGINATOR_ADDITIONAL_PAGES
TEST_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x02\x00"
    b"\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x02\x00\x01\x00\x00\x02\x02\x0C"
    b"\x0A\x00\x3B"
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='group-slug',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            id=42,
            image=SimpleUploadedFile(
                name="test_gif.gif", content=TEST_GIF, content_type="image/gif"
            ),
        )

        for x in range(42):
            cls.post = Post.objects.create(
                text=f'Пост {x}',
                author=cls.user,
                group=cls.group,
            )

        cls.special_group = Group.objects.create(
            title='Необычная группа',
            slug='special-group-slug',
            description='Необычное описание',
        )

        cls.special_post = Post.objects.create(
            text='Необычный пост',
            author=cls.user,
            id=420,
            group=cls.special_group
        )

        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': 'group-slug'},
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': 'auth'},
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': 42},
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }

    @classmethod
    def setUp(self) -> None:
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Индексная страница  с корректным контекстом."""
        response = self.auth_client.get(reverse('posts:index'))
        total_posts_on_page = len(response.context['page_obj'])

        self.assertEqual(total_posts_on_page, 10)
        self.assertIn('page_obj', response.context)

    def test_group_list_page_show_correct_context(self):
        """Список постов группы  с корректным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'group-slug'},
            )
        )

        first_object = response.context['page_obj'][0]
        total_posts_on_page = len(response.context['page_obj'])

        self.assertEqual(total_posts_on_page, POSTS_ON_PAGE)
        self.assertIn('page_obj', response.context)
        self.assertEqual(
            first_object.group.title,
            self.group.title,
        )
        self.assertEqual(
            first_object.group.description,
            self.group.description,
        )
        self.assertEqual(
            first_object.group.slug,
            self.group.slug,
        )

    def test_profile_page_show_correct_context(self):
        """Профиль  с корректным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'},
            )
        )

        first_object = response.context['page_obj'][0]
        total_posts_on_page = len(response.context['page_obj'])

        self.assertEqual(total_posts_on_page, 10)
        self.assertIn('page_obj', response.context)
        self.assertEqual(
            first_object.author.username,
            self.user.username,
        )

    def test_post_detail_page_show_correct_context(self):
        """Пост  с корректным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            )
        )

        first_object = response.context['post']

        self.assertEqual(
            first_object.text,
            self.post.text,
        )
        self.assertEqual(
            first_object.author.username,
            self.user.username,
        )
        self.assertEqual(
            first_object.group,
            self.post.group,
        )

    def test_post_create_page_show_correct_context(self):
        """Страница создания поста с корректным контекстом."""
        response = self.auth_client.get(reverse('posts:post_create'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Страница изменения поста с корректным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            )
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_special_post_on_three_pages(self):
        """Особый пост доступный на страницах index, profile, group_list."""
        page_names = {
            reverse('posts:index'): self.special_group.slug,
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.user.username
                }
            ): self.special_group.slug,
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.special_group.slug
                }
            ): self.special_group.slug,
        }

        for value, expected in page_names.items():
            response = self.auth_client.get(value)
            special_object = response.context['page_obj'][0]

            with self.subTest(value=value):
                self.assertEqual(special_object.group.slug, expected)

    def test_special_post_not_on_other_group_page(self):
        """Особый пост не доступный на странице чужой группы"""
        response = self.auth_client.get(
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.group.slug
                }
            )
        )

        usual_object = response.context['page_obj'][0]

        self.assertNotEqual(usual_object, self.special_post)
        self.assertNotEqual(usual_object.group.slug, self.special_group.slug)


class PaginatorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        list_of_posts: List[Post] = []

        cls.guest_client = Client()

        cls.user = User.objects.create(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group-slug',
            description='Тестовое описание',
        )

        for x in range(POSTS_ON_PAGE_FOR_TEST):
            list_of_posts.append(
                Post(
                    text=f'Пост {x}',
                    author=cls.user,
                    group=cls.group,
                )
            )

        Post.objects.bulk_create(list_of_posts)

        group_page = '/group/group-slug/'
        profile_page = '/profile/auth/'
        main_page = '/'
        second_page = '?page=2'

        cls.expected_page_state = {
            group_page: POSTS_ON_PAGE,
            profile_page: POSTS_ON_PAGE,
            main_page: POSTS_ON_PAGE,
            group_page + second_page: PAGINATOR_ADDITIONAL_PAGES,
            profile_page + second_page: PAGINATOR_ADDITIONAL_PAGES,
            main_page + second_page: PAGINATOR_ADDITIONAL_PAGES,
        }

    @classmethod
    def setUp(self) -> None:
        cache.clear()

    def test_paginator(self):
        """Проверка пагинатора."""
        for address, expected_posts in self.expected_page_state.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                total_posts_on_page = len(response.context['page_obj'])

                self.assertEqual(total_posts_on_page, expected_posts)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CachedPostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='group-slug',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            id=42,
            image=SimpleUploadedFile(
                name="test_gif.gif", content=TEST_GIF, content_type="image/gif"
            ),
        )

        for x in range(42):
            cls.post = Post.objects.create(
                text=f'Пост {x}',
                author=cls.user,
                group=cls.group,
            )

    @classmethod
    def setUp(self) -> None:
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_cache_on_main_page(self):
        """Тестирование кэша"""
        cached_page = self.guest_client.get(reverse("posts:index")).content
        Post.objects.all().delete()
        still_cached_page = (
            self.guest_client.get(reverse("posts:index")).content
        )

        self.assertEqual(cached_page, still_cached_page)

        cache.clear()
        non_cached_page = self.guest_client.get(reverse("posts:index")).content

        self.assertNotEqual(cached_page, non_cached_page)


class FollowingTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.user_not_follower = User.objects.create(username='not-follower')
        cls.auth_client_not_follower = Client()
        cls.auth_client_not_follower.force_login(cls.user_not_follower)

        cls.user_author = User.objects.create(username='author')
        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.user_author)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='group-slug',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            id=42,
            image=SimpleUploadedFile(
                name="test_gif.gif", content=TEST_GIF, content_type="image/gif"
            ),
        )

        for x in range(42):
            cls.post = Post.objects.create(
                text=f'Пост {x}',
                author=cls.user,
                group=cls.group,
            )

        cls.special_group = Group.objects.create(
            title='Необычная группа',
            slug='special-group-slug',
            description='Необычное описание',
        )

        cls.special_post = Post.objects.create(
            text='Необычный пост',
            author=cls.user,
            id=420,
            group=cls.special_group
        )

        cls.post_for_follower = Post.objects.create(
            text='Пост для подписки.',
            author=cls.user_author,
            group=cls.group
        )

    @classmethod
    def setUp(self) -> None:
        cache.clear()

    def test_profile_follow_authorized(self):
        """Авторизованный пользователь может подписаться на автора"""
        self.auth_client.get(
            reverse(
                "posts:profile_follow", args=[self.user_author.username]
            )
        )

        follower_number = Follow.objects.filter(
                                               user=self.user,
                                               author=self.user_author,
                                               ).count()

        self.assertEqual(follower_number, 1)

    def test_profile_stop_follow_authorized(self):
        """Авторизованный пользователь может отписаться от автора"""
        Follow.objects.create(author=self.user_author, user=self.user)

        self.auth_client.get(
            reverse(
                "posts:profile_unfollow", args=[self.user_author.username]
            )
        )

        follower_number = Follow.objects.filter(
            user=self.user,
            author=self.user_author,
        ).count()

        self.assertEqual(follower_number, 0)
        self.assertFalse(
            Follow.objects.filter(
                author=self.user_author,
                user=self.user
            ).exists())

    def test_new_post_appears_for_follower(self):
        """Новые посты автора показываются на странице подписок"""
        Follow.objects.create(author=self.user_author, user=self.user)

        response = self.auth_client.get(reverse("posts:follow_index"))

        self.assertEqual(
            self.post_for_follower,
            response.context['page_obj'][0]
        )

    def test_new_post_not_appear_for_non_follower(self):
        """Новые посты автора не показываются на странице подписок"""
        Post.objects.create(
            text='Пост для подписки.',
            author=self.user,
            group=self.group
        )
        response = self.auth_client_not_follower.get(
            reverse("posts:follow_index")
        )

        self.assertFalse(len(response.context['page_obj']), 0)

    def test_auth_user_cant_self_follow(self):
        """Авторизованный пользователь не может подписаться сам на себя"""
        self.auth_client.get(
            reverse(
                "posts:profile_follow", args=[self.user.username]
            )
        )

        follower_number = Follow.objects.filter(
                                               user=self.user,
                                               author=self.user,
                                               ).count()

        self.assertEqual(follower_number, 0)
