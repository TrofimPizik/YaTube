from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_group_have_correct_object_names(self):
        task_group = self.group
        expected_object_name = task_group.title
        self.assertEqual(expected_object_name, str(task_group))

    def test_post_have_correct_object_names(self):
        task_post = self.post
        expected_object_name = task_post.text
        self.assertEqual(expected_object_name, str(task_post))
