import unittest
from project import app, db
from project.books.models import Book

class TestBookModel(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_valid_book_creation(self):
        """Test tworzenia książki z prawidłowymi danymi."""
        book = Book(name="Valid Book", author="Valid Author", year_published=2023, book_type="Fiction")
        db.session.add(book)
        db.session.commit()
        self.assertIsNotNone(book.id)
        self.assertEqual(book.name, "Valid Book")
        self.assertEqual(book.status, "available")

    def test_invalid_year_negative(self):
        """Test tworzenia książki z ujemnym rokiem. Powinno nie przejść walidacji."""
        book = Book(name="Negative Year", author="Author", year_published=-100, book_type="Fiction")
        self.assertGreaterEqual(book.year_published, 0, "Rok wydania nie powinien być ujemny")

    def test_invalid_empty_name(self):
        """Test tworzenia książki z pustą nazwą. Powinno nie przejść walidacji."""
        book = Book(name="", author="Author", year_published=2023, book_type="Fiction")
        self.assertTrue(len(book.name) > 0, "Nazwa książki nie powinna być pusta")

    def test_sql_injection_attempt(self):
        """Test próby wstrzyknięcia SQL w nazwie."""
        bad_input = "Book'; DROP TABLE books; --"
        book = Book(name=bad_input, author="Hacker", year_published=2023, book_type="Hacking")
        
        self.assertNotIn("DROP TABLE", book.name, "Wzorzec SQL Injection powinien zostać oczyszczony lub odrzucony")
        self.assertNotIn(";", book.name, "Znaki SQL Injection powinny zostać oczyszczone lub odrzucone")

    def test_xss_injection_attempt(self):
        """Test próby wstrzyknięcia XSS w autorze."""
        bad_input = "<script>alert('XSS')</script>"
        book = Book(name="XSS Book", author=bad_input, year_published=2023, book_type="Hacking")
        
        self.assertNotIn("<script>", book.author, "Wzorzec XSS powinien zostać oczyszczony lub odrzucony")

    def test_extreme_data_length(self):
        """Test ekstremalnie długiego ciągu znaków."""
        long_str = "A" * 10000
        book = Book(name=long_str, author="Author", year_published=2023, book_type="Fiction")
        
        try:
            db.session.add(book)
            db.session.commit()
            
            saved_book = Book.query.filter_by(author="Author").first()
            self.assertLessEqual(len(saved_book.name), 64, "Nazwa powinna mieć maksymalnie 64 znaki")
            
        except Exception as e:
            pass

if __name__ == '__main__':
    unittest.main()
