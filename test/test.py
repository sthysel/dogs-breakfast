# -*- coding: utf-8 -*-
import os
import unittest
import epub


TEST_XHTML_MIMETYPE = u'application/xhtml+xml'


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
            self.assertEqual(with_book.opf.metadata.languages, [u'en'])
            self.assertEqual(with_book.opf.metadata.titles,
                             [(u'Testing Epub', '')])
            self.assertEqual(len(with_book.opf.manifest), 7)
            for key, item in with_book.opf.manifest.iteritems():
                self.assertEqual(item.identifier, key)
                self.assertIsInstance(item, epub.opf.ManifestItem)


class TestFunctionWriteMode(unittest.TestCase):

    epub_path = u'_data/write/test.epub'
    xhtml_item_path = u'_data/write/add_item.xhtml'

    def _subtest_add_item(self, book):
        """Test very basic add_item feature.

        The purpose of this subtest is to test a very few basic featureset
        that are common to both [w]rite and [a]ppend mode.
        """
        # Test if we realy are in write/append mode
        self.assertIn(book.mode, [u'a', u'w'])

        filename = os.path.join(os.path.dirname(__file__),
                                self.xhtml_item_path)
        manifest_item = epub.opf.ManifestItem(identifier=u'AddItem0001',
                                              href=u'Text/add_item.xhtml',
                                              media_type=TEST_XHTML_MIMETYPE)
        book.add_item(filename, manifest_item)

        with open(filename, u'r') as f:
            expected_data = f.read().decode(u'utf-8')
        result_data = book.read_item(manifest_item).decode(u'utf-8')

        self.assertIn(manifest_item, book.opf.manifest)
        self.assertEqual(result_data, expected_data)


class TestFunctionWriteModeNew(TestFunctionWriteMode):

    def setUp(self):
        self._clean_files()

    def tearDown(self):
        self._clean_files()

    def _clean_files(self):
        filename = os.path.join(os.path.dirname(__file__), self.epub_path)
        if os.path.isfile(filename):
            os.remove(filename)

    def test_open(self):
        working_copy_filename = os.path.join(os.path.dirname(__file__),
                                             self.epub_path)

        # test that the file is correctly open in [a]ppend mode.
        book = epub.open(working_copy_filename, u'w')
        self.assertEqual(book.opf_path, u'OEBPS/content.opf')
        self.assertEqual(book.content_path, u'OEBPS')
        self.assertEqual(book.opf.metadata.languages, [])
        self.assertEqual(book.opf.metadata.titles, [])
        self.assertEqual(len(book.opf.manifest), 1)
        # 1 meta file: mimetype
        # 0 content file
        self.assertEqual(len(book.namelist()), 1)

        self._subtest_add_item(book)
        book.close()


class TestFunctionWriteModeAppend(TestFunctionWriteMode):

    epub_source = u'_data/write/source.epub'
    epub_empty = u'_data/write/test_empty.epub'

    def setUp(self):
        """Create a copy of source epub."""
        source_filename = os.path.join(os.path.dirname(__file__),
                                       self.epub_source)
        working_copy_filename = os.path.join(os.path.dirname(__file__),
                                             self.epub_path)
        with open(source_filename) as source:
            with open(working_copy_filename, u'w') as working_copy:
                working_copy.write(source.read())

        self._clean_files()

    def tearDown(self):
        """Destroy copy of source epub."""
        working_copy_filename = os.path.join(os.path.dirname(__file__),
                                             self.epub_path)
        if os.path.isfile(working_copy_filename):
            os.remove(working_copy_filename)

        self._clean_files()

    def _clean_files(self):
        working_empty_filename = os.path.join(os.path.dirname(__file__),
                                             self.epub_empty)
        if os.path.isfile(working_empty_filename):
            os.remove(working_empty_filename)

    def test_open(self):
        working_copy_filename = os.path.join(os.path.dirname(__file__),
                                             self.epub_path)

        # test that the file is correctly open in [a]ppend mode.
        book = epub.open(working_copy_filename, u'a')
        self.assertEqual(book.opf_path, u'OEBPS/content.opf')
        self.assertEqual(book.content_path, u'OEBPS')
        self.assertEqual(book.opf.metadata.languages, [u'fr'])
        self.assertEqual(book.opf.metadata.titles, [(u'Il était une fois...', '')])
        self.assertEqual(len(book.opf.manifest), 2)
        # 4 meta files: mimetype, container.xml, content.opf, toc.ncx,
        # 1 content file: Section0001.xhtml
        self.assertEqual(len(book.namelist()), 5)

        self._subtest_add_item(book)
        book.close()

    def test_open_new(self):
        working_copy_filename = os.path.join(os.path.dirname(__file__),
                                             self.epub_empty)

        # test that the file is correctly open in [a]ppend mode.
        book = epub.open(working_copy_filename, u'a')
        self.assertEqual(book.opf_path, u'OEBPS/content.opf')
        self.assertEqual(book.content_path, u'OEBPS')
        self.assertEqual(book.opf.metadata.languages, [])
        self.assertEqual(book.opf.metadata.titles, [])
        self.assertEqual(len(book.opf.manifest), 1)
        # 1 meta file: mimetype
        # 0 content file
        self.assertEqual(len(book.namelist()), 1)

        self._subtest_add_item(book)
        book.close()


class TestEpubFile(unittest.TestCase):
    """Test class for epub.EpubFile class"""

    epub_path = u'_data/test.epub'

    def setUp(self):
        test_path = os.path.join(os.path.dirname(__file__), self.epub_path)
        self.epub_file = epub.open(test_path)

    def tearDown(self):
        self.epub_file.close()

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

    def test_add_item_fail(self):
        """When open in read-only mode, add_item must fail."""
        with self.assertRaises(IOError):
            filename = u'_data/write/add_item.xhtml'
            manifest_item = epub.opf.ManifestItem(identifier=u'AddItem0001',
                                                  href=u'Text/add_item.xhtml',
                                                  media_type=TEST_XHTML_MIMETYPE)
            self.epub_file.add_item(filename, manifest_item)

        self.epub_file.close()
        with self.assertRaises(RuntimeError):
            filename = u'_data/write/add_item.xhtml'
            manifest_item = epub.opf.ManifestItem(identifier=u'AddItem0001',
                                                  href=u'Text/add_item.xhtml',
                                                  media_type=TEST_XHTML_MIMETYPE)
            self.epub_file.add_item(filename, manifest_item)
