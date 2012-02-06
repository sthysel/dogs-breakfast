# -*- coding: utf-8 -*-

"""
Library to open and read files in the epub version 2.
"""

__author__ = u'Florian Strzelecki <florian.strzelecki@gmail.com>'
__version__ = u'0.1.1'

import os
import zipfile

from xml.dom import minidom

from epub import ncx

MIMETYPE_OPF = u'application/oebps-package+xml'
MIMETYPE_NCX = u'application/x-dtbncx+xml'

def open(filename):
    """Open an epub file and return an EpubFile object

    File is opened read-only.
    """
    book = EpubFile(zip=zipfile.ZipFile(filename))

    # Read container.xml to get OPF xml file path
    xmlstring = book.zip.read('META-INF/container.xml')
    container_xml = minidom.parseString(xmlstring).documentElement

    for e in container_xml.getElementsByTagName('rootfile'):
        if e.getAttribute('media-type') == MIMETYPE_OPF:
            book.opf_path = e.getAttribute('full-path')
            break

    # Read OPF xml file
    xmlstring = book.zip.read(book.opf_path)
    package = minidom.parseString(xmlstring).documentElement

    # Store each child nodes into a dict (metadata, manifest, spine, guide)
    data = {}
    for node in [e for e in package.childNodes if e.nodeType == e.ELEMENT_NODE]:
        data[node.tagName.lower()] = node

    # Inspect metadata
    book.metadata = _parse_xml_metadata(data['metadata'])

    # Get Uid
    book.uid_id = package.getAttribute('unique-identifier')
    book.uid = [x for x in book.metadata.identifier if x[1] == book.uid_id][0]

    # Inspect manifest
    book.manifest = _parse_xml_manifest(data['manifest'])

    # Inspect spine
    item_toc = book.get_item(data['spine'].getAttribute('toc'))
    book.spine = _parse_xml_spine(data['spine'])

    # Inspect guide if exist
    if 'guide' in data:
        book.guide = _parse_xml_guide(data['guide'])

    # Inspect NCX toc file
    book.toc = ncx.parse_toc(book.read(item_toc))

    return book

def _parse_xml_metadata(element):
    """Extract metadata from an xml.dom.Element object (ELEMENT_NODE)

    The "<metadata>" tag has a lot of metadatas about the epub this method 
    inspect and store into object attributes (like "title" or "creator").
    """
    metadata = EpubMetadata()

    for node in element.getElementsByTagName(u'dc:title'):
        node.normalize()
        metadata.add_title(node.firstChild.data, node.getAttribute(u'xml:lang'))

    for node in element.getElementsByTagName(u'dc:creator'):
        node.normalize()
        metadata.add_creator(node.firstChild.data,
                         node.getAttribute(u'opf:role'),
                         node.getAttribute(u'opf:file-as'))

    for node in element.getElementsByTagName(u'dc:subject'):
        node.normalize()
        metadata.add_subject(node.firstChild.data)

    for node in element.getElementsByTagName(u'dc:description'):
        node.normalize()
        metadata.description = node.firstChild.data

    for node in element.getElementsByTagName(u'dc:publisher'):
        node.normalize()
        metadata.publisher = node.firstChild.data

    for node in element.getElementsByTagName(u'dc:contributor'):
        node.normalize()
        metadata.add_contributor(node.firstChild.data,
                             node.getAttribute(u'opf:role'),
                             node.getAttribute(u'opf:file-as'))

    for node in element.getElementsByTagName(u'dc:date'):
        node.normalize()
        metadata.add_date(node.firstChild.data,
                          node.getAttribute(u'opf:event'))

    for node in element.getElementsByTagName(u'dc:type'):
        node.normalize()
        metadata.type = node.firstChild.data

    for node in element.getElementsByTagName(u'dc:format'):
        node.normalize()
        metadata.format = node.firstChild.data

    for node in element.getElementsByTagName(u'dc:identifier'):
        node.normalize()
        metadata.add_identifier(node.firstChild.data,
                            node.getAttribute(u'id'),
                            node.getAttribute(u'opf:scheme'))

    for node in element.getElementsByTagName(u'dc:source'):
        node.normalize()
        metadata.source = node.firstChild.data

    for node in element.getElementsByTagName(u'dc:language'):
        node.normalize()
        metadata.add_language(node.firstChild.data)

    for node in element.getElementsByTagName(u'dc:relation'):
        node.normalize()
        metadata.relation = node.firstChild.data

    for node in element.getElementsByTagName(u'dc:coverage'):
        node.normalize()
        metadata.coverage = node.firstChild.data

    for node in element.getElementsByTagName(u'dc:rights'):
        node.normalize()
        metadata.rights = node.firstChild.data

    for node in element.getElementsByTagName(u'meta'):
        metadata.add_meta(node.getAttribute(u'name'),
                      node.getAttribute(u'content'))

    return metadata

def _parse_xml_manifest(element):
    """Inspect an xml.dom.Element <manifest> and return a list of 
    epub.EpubManifestItem object."""

    manifest = []
    for e in element.getElementsByTagName('item'):
        item = EpubManifestItem(e.getAttribute('id'),
                                e.getAttribute('href'),
                                e.getAttribute('media-type'),
                                e.getAttribute('fallback'),
                                e.getAttribute('required-namespace'),
                                e.getAttribute('required-modules'),
                                e.getAttribute('fallback-style'))
        manifest.append(item)
    return manifest

def _parse_xml_spine(element):
    """Inspect an xml.dom.Element <spine> and return a list of itemref as tuple.
    """

    spine = []
    for e in element.getElementsByTagName('itemref'):
        spine.append((e.getAttribute('idref'),
                      e.getAttribute('linear').lower() != 'no'))
    return spine

def _parse_xml_guide(element):
    """Inspect an xml.dom.Element <guide> and return a list of ref as tuple."""

    guide = []
    for e in element.getElementsByTagName('ref'):
        guide.append((e.getAttribute('href'),
                      e.getAttribute('type'),
                      e.getAttribute('title')))
    return guide


class EpubFile(object):
    """Represents an epub file as described in version 2.0.1
    
    See http://idpf.org/epub/201"""

    zip = None
    opf_path = None
    uid = None
    uid_id = None
    metadata = None
    manifest = None
    spine = None
    guide = None
    toc = None

    def __init__(self, zip=None):
        self.zip = zip
        self.opf_path = None
        self.uid = None
        self.uid_id = None
        self.metadata = None
        self.manifest = []
        self.spine = []
        self.guide = []
        toc = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    #
    # Manifest, spine & guide
    #

    def add_item(self, id, href, media_type=None, fallback=None, 
                 required_namespace=None, required_modules=None, 
                 fallback_style=None):
        item = EpubManifestItem(id, href, media_type,
                                fallback, required_namespace, required_modules,
                                fallback_style)
        self.manifest.append(item)

    def add_spine_itemref(self, idref, linear=True):
        self.spine.append((idref, linear))

    def get_item(self, id):
        """Get an item from manifest through its "id" attribute.
        
        Return an EpubManifestItem if found, else None."""
        l = [x for x in self.manifest if x.id == id]
        if l:
            return l[0]
        else:
            return None

    def get_item_by_href(self, href):
        """Get an item from manifest through its "href" attribute.
        
        Return an EpubManifestItem if found, else None."""
        l = [x for x in self.manifest if x.href == href]
        if l:
            return l[0]
        else:
            return None

    def add_guide_ref(self, href, type, title):
        self.guide.append((href, type, title))

    #
    # Traitement et lecture des fichiers
    #

    def read(self, item):
        """Read a file from the epub zipfile container.
        
        "item" parameter can be the relative path to the opf file or an 
        EpubManifestItem object.
        
        Html fragments are not acceptable : the path must be exactly the same 
        as indicated in the opf file.
        """
        path = item
        if isinstance(item, EpubManifestItem):
            path = item.href
        dirpath = os.path.dirname(self.opf_path)
        return self.zip.read(os.path.join(dirpath, path))

    def close(self):
        """Close the zipfile archive.
        
        Not very usefull yet, because zipfile is open in read-only."""
        self.zip.close()


class EpubMetadata(object):
    """Represent an epub's metadatas set.
    
    See http://idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#Section2.2"""

    title = []
    creator = []
    subject = []
    description = None
    publisher = None
    contributor = []
    date = []
    type = None
    format = None
    identifier = []
    source = None
    language = []
    relation = None
    coverage = None
    rights = None
    meta = []

    def __init__(self):
        self.title = []
        self.creator = []
        self.subject = []
        self.description = None
        self.publisher = None
        self.contributor = []
        self.date = []
        self.type = None
        self.format = None
        self.identifier = []
        self.source = None
        self.language = []
        self.relation = None
        self.coverage = None
        self.rights = None
        self.meta = []

    def add_title(self, title, lang=''):
        self.title.append((title, lang))

    def add_creator(self, name, role=u'aut', file_as=u''):
        self.creator.append((name, role, file_as))

    def add_subject(self, subject):
        self.subject.append(subject)

    def add_contributor(self, name, role=u'oth', file_as=u''):
        self.contributor.append((name, role, file_as))

    def add_date(self, date, event=''):
        self.date.append((date, event))

    def add_identifier(self, content, id=u'', scheme=u''):
        self.identifier.append((content, id, scheme))

    def add_language(self, lang):
        self.language.append(lang)

    def add_meta(self, name, content):
        self.meta.append((name, content))

    def get_isbn(self):
        l = [id[0] for id in self.identifier if id[2].lower() == u'isbn']
        isbn = None
        if l:
            isbn = l[0]
        return isbn

    def as_xml_element(self):
        """Return an xml dom Element node."""
        doc = minidom.Document()
        metadata = doc.createElement('metadata')

        for text, lang in self.title:
            title = doc.createElement('dc:title')
            if lang:
                title.setAttribute('xml:lang', lang)
            title.appendChild(doc.createTextNode(text))
            metadata.appendChild(title)

        for name, role, file_as in self.creator:
            creator = doc.createElement('dc:creator')
            creator.setAttribute('opf:role', role)
            if file_as:
                creator.setAttribute('opf:file-as', file_as)
            creator.appendChild(doc.createTextNode(name))
            metadata.appendChild(creator)

        for text in self.subject:
            subject = doc.createElement('dc:subject')
            subject.appendChild(doc.createTextNode(text))
            metadata.appendChild(subject)

        if self.description:
            description = doc.createElement('dc:description')
            description.appendChild(doc.createTextNode(self.description))
            metadata.appendChild(description)

        if self.publisher:
            publisher = doc.createElement('dc:publisher')
            publisher.appendChild(doc.createTextNode(self.publisher))
            metadata.appendChild(publisher)

        for name, role, file_as in self.contributor:
            contributor = doc.createElement('dc:creator')
            contributor.setAttribute('opf:role', role)
            if file_as:
                contributor.setAttribute('opf:file-as', file_as)
            contributor.appendChild(doc.createTextNode(name))
            metadata.appendChild(contributor)

        for text, event in self.date:
            date = doc.createElement('dc:date')
            if event:
                date.setAttribute('opf:event', event)
            date.appendChild(doc.createTextNode(text))
            metadata.appendChild(date)

        if self.type:
            type = doc.createElement('dc:type')
            type.appendChild(doc.createTextNode(self.type))
            metadata.appendChild(type)

        if self.format:
            format = doc.createElement('dc:format')
            format.appendChild(doc.createTextNode(self.format))
            metadata.appendChild(format)

        for text, id, scheme in self.identifier:
            identifier = doc.createElement('dc:identifier')
            if id:
                identifier.setAttribute('id', id)
            if scheme:
                identifier.setAttribute('opf:scheme', scheme)
            identifier.appendChild(doc.createTextNode(text))
            metadata.appendChild(identifier)

        if self.source:
            source = doc.createElement('dc:source')
            source.appendChild(doc.createTextNode(self.source))
            metadata.appendChild(source)

        for text in self.language:
            language = doc.createElement('dc:language')
            language.appendChild(doc.createTextNode(text))
            metadata.appendChild(language)

        if self.relation:
            relation = doc.createElement('dc:relation')
            relation.appendChild(doc.createTextNode(self.relation))
            metadata.appendChild(relation)

        if self.coverage:
            coverage = doc.createElement('dc:coverage')
            coverage.appendChild(doc.createTextNode(self.coverage))
            metadata.appendChild(coverage)

        if self.rights:
            rights = doc.createElement('dc:rights')
            rights.appendChild(doc.createTextNode(self.rights))
            metadata.appendChild(rights)

        for name, content in self.meta:
            meta = doc.createElement('meta')
            meta.setAttribute('name', name)
            meta.setAttribute('content', content)
            metadata.appendChild(meta)

        return metadata


class EpubManifestItem(object):
    """Represent an item from the epub's manifest."""

    id = None
    href = None
    media_type = None
    fallback = None
    required_namespace = None
    required_modules = None
    fallback_style = None

    def __init__(self, id, href, media_type=None, fallback=None, 
                 required_namespace=None, required_modules=None, 
                 fallback_style=None):
        self.id = id
        self.href = href
        self.media_type = media_type
        self.fallback = fallback
        self.required_namespace = required_namespace
        self.required_modules = required_modules
        self.fallback_style = fallback_style

    def as_xml_element(self):
        """Return an xml dom Element node."""

        item = minidom.Document().createElement("item")

        item.setAttribute('id', self.id)
        item.setAttribute('href', self.href)
        if self.media_type:
            item.setAttribute('media_type', self.media_type)
        if self.fallback:
            item.setAttribute('fallback', self.fallback)
        if self.required_namespace:
            item.setAttribute('required_namespace', self.required_namespace)
        if self.required_modules:
            item.setAttribute('required_modules', self.required_modules)
        if self.fallback_style:
            item.setAttribute('fallback_style', self.fallback_style)

        return item

