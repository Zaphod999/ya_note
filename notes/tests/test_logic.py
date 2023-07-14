from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):

    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Залогиненный')
        cls.reader = User.objects.create(username='Незалогиненный')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.form_data = {
            'title': 'Тестовый заголовок',
            'text': cls.NOTE_TEXT,
            'slug': 'test-slug',
        }

    def test_anonymous_user_cant_create_note(self):
        """
        Анонимный пользователь не может создать заметку.
        """
        url = reverse('notes:add')
        self.client.post(url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_logged_in_user_can_create_note(self):
        """
        Залогиненный пользователь может создать заметку.
        """
        url = reverse('notes:add')
        response = self.auth_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.text, self.NOTE_TEXT)
        self.assertEqual(new_note.author, self.author)
