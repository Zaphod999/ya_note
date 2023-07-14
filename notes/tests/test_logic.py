from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

from pytils.translit import slugify

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

    def test_not_unique_slug(self):
        """
        Невозможно создать две заметки с одинаковым slug.
        """
        form_data_2 = {
            'title': 'Тестовый заголовок 2',
            'text': self.NOTE_TEXT+' 2',
            'slug': 'test-slug2',
        }
        url = reverse('notes:add')
        self.auth_client.post(url, data=self.form_data)
        self.assertEqual(Note.objects.count(), 1)
        form_data_2['slug'] = Note.objects.get().slug
        response = self.auth_client.post(url, data=form_data_2)
        self.assertEqual(Note.objects.count(), 1)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=Note.objects.get().slug + WARNING
        )

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug, то он формируется
        автоматически, с помощью функции pytils.translit.slugify.
        """
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = self.auth_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор новости')
        cls.reader = User.objects.create(username='Читатель')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.test_note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='test-slug',
            author=cls.author,
        )
        cls.note_url = reverse(
            'notes:detail',
            kwargs={'slug': cls.test_note.slug}
        )
        cls.edit_url = reverse(
            'notes:edit',
            kwargs={'slug': cls.test_note.slug}
        )
        cls.delete_url = reverse(
            'notes:delete',
            kwargs={'slug': cls.test_note.slug}
        )
        cls.form_data = {
            'title': 'Исправленный заголовок',
            'text': 'Исправленный текст',
            'slug': 'edit-slug',
        }

    def test_author_can_delete_note(self):
        """
        Пользователь может удалить свою заметку
        """
        response = self.auth_client.delete(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_reader_cant_delete_note_of_another_user(self):
        """
        Пользователь не может удалить чужую заметку
        """
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """
        Пользователь может редактировать свою заметку
        """
        response = self.auth_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.test_note.refresh_from_db()
        self.assertEqual(self.test_note.text, 'Исправленный текст')

    def test_reader_cant_edit_note_of_another_user(self):
        """
        Пользователь не может редактировать чужую заметку
        """
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.test_note.refresh_from_db()
        self.assertEqual(self.test_note.text, 'Текст')
