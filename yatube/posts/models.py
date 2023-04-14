from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

POST_STR_DESC: int = 15


class Group(models.Model):
    title = models.CharField(
        'Название группы',
        max_length=200,
        help_text='Название группы',
    )
    slug = models.SlugField(
        'Ссылка группы',
        unique=True,
        help_text='Ссылка группы',
    )
    description = models.TextField(
        'Описание группы',
        help_text='Описание группы',
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Содержимое поста',
        help_text='Содержимое поста',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        help_text='Дата публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ['-pub_date', ]

    def __str__(self):
        return self.text[:POST_STR_DESC]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Комментарий',
        help_text='Комментарий',
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Автор',
    )
    text = models.TextField(
        'Содержимое комментария',
        help_text='Содержимое комментария',
    )
    created = models.DateTimeField(
        'Дата публикации комментария',
        auto_now_add=True,
        help_text='Дата публикации комментария',
    )

    class Meta:
        ordering = ['-created', ]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    def __str__(self):
        return f'{self.user.username} -> {self.author.username}'
