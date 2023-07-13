from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Hren')
        cls.reader = User.objects.create(username='Незалогиненный')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='def_slug',
            author=cls.author
        )

    def test_user_notes_in_list_for_different_users(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок в
        списке object_list в словаре context; в список заметок одного
        пользователя не попадают заметки другого пользователя.
        """
        user_note_in_list = (
            (self.author, True),
            (self.reader, False),
        )
        self.client.force_login(self.author)
        url = reverse('notes:list')
        for user, status in user_note_in_list:
            with self.subTest(user=user, name='notes:list'):
                self.client.force_login(user)
                response = self.client.get(url)
                object_list = response.context['object_list']
                self.assertEqual((self.note in object_list), status)

    def test_pages_contain_form(self):
        """
        На страницы создания и редактирования заметки передаются формы.
        """
        urls = (
            ('notes:add', None),
            ('notes:edit', {'slug': self.note.slug}),
        )
        self.client.force_login(self.author)
        for name, kwargs in urls:
            url = reverse(name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(('form' in response.context), True)
