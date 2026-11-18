import os
import tempfile
import datetime as dt
import unittest

import people_engine
from catalog_bridge import import_catalog, assign_book, reading_progress


class CatalogBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.temp.name, "people.sqlite3")
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.temp.cleanup()

    def test_import_and_assign_preserve_real_catalog_ids(self):
        self.assertEqual(import_catalog(self.db, [{"id":"catalog-17","title":"Örnek Kitap","author":"Örnek Yazar"}]), 1)
        assign_book(self.db, 1, "catalog-17")
        assign_book(self.db, 1, "catalog-17")
        self.assertEqual(reading_progress(self.db, 1)[0]["id"], "catalog-17")
        self.assertEqual(len(reading_progress(self.db, 1)), 1)
        self.assertEqual(reading_progress(self.db, 2), [])

    def test_hourly_tick_records_catalog_progress(self):
        import_catalog(self.db, [{"id":"real-book-1","title":"Gerçek Katalog Kaydı"}])
        result = people_engine.tick(self.db, dt.datetime(2026, 11, 18, 9, tzinfo=dt.timezone.utc))
        self.assertGreater(result["new"], 0)
        total = self.db.execute("SELECT COALESCE(SUM(minutes),0) FROM person_books").fetchone()[0]
        self.assertGreater(total, 0)
        self.assertEqual(people_engine.tick(self.db, dt.datetime(2026, 11, 18, 9, tzinfo=dt.timezone.utc))["new"], 0)
        self.assertEqual(self.db.execute("SELECT COALESCE(SUM(minutes),0) FROM person_books").fetchone()[0], total)

    def test_reject_unknown_books_and_people(self):
        with self.assertRaises(ValueError):
            assign_book(self.db, 1, "not-imported")
        import_catalog(self.db, [{"id":"b","title":"Test"}])
        with self.assertRaises(ValueError):
            assign_book(self.db, 999, "b")

    def test_invalid_catalog_does_not_partially_import(self):
        with self.assertRaises(ValueError):
            import_catalog(self.db, [{"id":"ok","title":"Test"},{"id":"","title":"Invalid"}])
        self.assertEqual(self.db.execute("SELECT count(*) FROM catalog_books").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
