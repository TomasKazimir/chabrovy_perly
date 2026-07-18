import tempfile
import unittest

from app import create_app


class QuotesAppTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": self.tmp_db.name,
                "SECRET_KEY": "test",
                "ADMIN_USERNAME": "admin",
                "ADMIN_PASSWORD": "secret",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp_db.close()

    def login(self):
        return self.client.post(
            "/admin/login",
            data={"username": "admin", "password": "secret"},
            follow_redirects=True,
        )

    def test_main_page_shows_quotes_ordered_by_date(self):
        self.login()
        self.client.post(
            "/admin/quotes/new",
            data={"quote_date": "2024-01-01", "text": "Older quote"},
            follow_redirects=True,
        )
        self.client.post(
            "/admin/quotes/new",
            data={"quote_date": "2024-05-01", "text": "Newer quote"},
            follow_redirects=True,
        )

        response = self.client.get("/")
        content = response.get_data(as_text=True)

        self.assertLess(content.index("Newer quote"), content.index("Older quote"))

    def test_search_by_substring_and_date(self):
        self.login()
        self.client.post(
            "/admin/quotes/new",
            data={"quote_date": "2024-06-10", "text": "Banana wisdom"},
            follow_redirects=True,
        )
        self.client.post(
            "/admin/quotes/new",
            data={"quote_date": "2024-06-11", "text": "Apple joke"},
            follow_redirects=True,
        )

        by_text = self.client.get("/?q=banana")
        self.assertIn("Banana wisdom", by_text.get_data(as_text=True))
        self.assertNotIn("Apple joke", by_text.get_data(as_text=True))

        by_date = self.client.get("/?date=2024-06-11")
        self.assertIn("Apple joke", by_date.get_data(as_text=True))
        self.assertNotIn("Banana wisdom", by_date.get_data(as_text=True))

    def test_admin_must_login_and_can_edit(self):
        redirected = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(302, redirected.status_code)

        self.login()
        self.client.post(
            "/admin/quotes/new",
            data={"quote_date": "2024-07-01", "text": "Original"},
            follow_redirects=True,
        )
        edit = self.client.post(
            "/admin/quotes/1/edit",
            data={"quote_date": "2024-07-02", "text": "Updated"},
            follow_redirects=True,
        )
        content = edit.get_data(as_text=True)

        self.assertIn("Updated", content)
        self.assertIn("2024-07-02", content)


if __name__ == "__main__":
    unittest.main()
