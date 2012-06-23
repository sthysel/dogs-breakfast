# -*- coding: utf-8 -*-

import os
import unittest
import epub

from xml.dom import minidom

class TestFunction(unittest.TestCase):
    epub_path = u'_data/test.epub'

    def test_open(self):
        test_path = os.path.join(os.path.dirname(__file__), self.epub_path)
        book = epub.open(test_path)

        self.assertEqual(book.opf_path, u'OEBPS/content.opf')
        self.assertEqual(book.content_path, u'OEBPS')
        self.assertEqual(book.opf.metadata.languages, [u'en'])
        self.assertEqual(book.opf.metadata.titles, [(u'Testing Epub', '')])
        self.assertEqual(len(book.opf.manifest), 7)

        for key, item in book.opf.manifest.iteritems():
            self.assertEqual(item.identifier, key)
            self.assertIsInstance(item, epub.opf.ManifestItem)

        with epub.open(test_path) as with_book:
            self.assertEqual(with_book.opf.metadata.languages, [u'en',])
            self.assertEqual(with_book.opf.metadata.titles, [(u'Testing Epub', ''),])
            self.assertEqual(len(with_book.opf.manifest), 7)
            for key, item in with_book.opf.manifest.iteritems():
                self.assertEqual(item.identifier, key)
                self.assertIsInstance(item, epub.opf.ManifestItem)


class TestEpubFile(unittest.TestCase):
    """Test class for epub.EpubFile class"""

    epub_path = u'_data/test.epub'

    def setUp(self):
        test_path = os.path.join(os.path.dirname(__file__), self.epub_path)
        self.epub_file = epub.open(test_path)

    def test_get_item(self):
        """Check EpubFile.get_item() return an EpubManifestItem by its id"""
        item = self.epub_file.get_item('Section0002.xhtml')
        self.assertIsInstance(item, epub.opf.ManifestItem,
                              u'L\'item retourné doit être un objet de type <epub.opf.ManifestItem>')
        self.assertEqual(item.identifier, u'Section0002.xhtml', u'id attendu incorrect.')
        self.assertEqual(item.href, u'Text/Section0002.xhtml',
                         u'href attendu incorrect.')

        self.assertEqual(self.epub_file.get_item(u'BadId'), None)

    def test_get_item_by_ref(self):
        """Check EpubFile.get_item() return an EpubManifestItem by its href"""
        item = self.epub_file.get_item_by_href(u'Text/Section0002.xhtml')
        self.assertIsInstance(item, epub.opf.ManifestItem,
                              u'L\'item retourné doit être un objet de type <epub.opf.ManifestItem>')
        self.assertEqual(item.identifier, u'Section0002.xhtml', u'id attendu incorrect.')
        self.assertEqual(item.href, u'Text/Section0002.xhtml',
                         u'href attendu incorrect.')

        self.assertEqual(self.epub_file.get_item_by_href(u'BadHref'), None)

        # Change only Id, so there is 2 item with the same href attribute
        item.identifier = u'CopyOfSection0002.xhtml'
        self.epub_file.opf.manifest.append(item)

        with self.assertRaises(LookupError):
            self.epub_file.get_item_by_href(item.href)
