import os
import copy
from pathlib import Path

from . import matcher

# - ordering: list of strings, which if supplied, will be used to
#   determine the order the content is read in
# TODO:
# have an `orderer` input class, which lets you:
# - set ordering of each file 
#       menu will say something like: `displays files with indexes`
#       - type number of file number X or z to be done
#       (X increments as this loops)
# - exclude files
#       menu will say something like: `displays files with indexes`
#       - type number of file to exclude or z to be done

class TextReader():
    def __init__(self, storage, path=None):
        """
        parameters:
        - path: path to where the text is. currently supports directories,
          a file, and an epub
        """
        self.storage = storage

        stored_textobject = self.storage.metadata.get('TextObject')
        if stored_textobject:
            self.load_from_storage(stored_textobject)
        else:
            self.load_from_path(path)

        self.update_storage()

    @property
    def ordered_content_files(self):
        ordered_content = self.storage.metadata['files']['ordering']
        for file_name in self.files:
            if file_name in self.storage.metadata['files']['exclusions']:
                continue

            if file_name in self.storage.metadata['files']['ordering']:
                continue

            ordered_content.append(file_name)

        return ordered_content

    def load_matches(self, reload=False, entities_with_aliases=None):
        entity_matcher = matcher.EntityMatchObject(entities_with_aliases)
        for file_name in self.ordered_content_files:
            raw_matches = self.storage.raw_matches.get(file_name, None)
            if raw_matches is None or reload:
                file_text = self.get_file_content(file_name)
                raw_matches = entity_matcher.get_matches(file_text)

                self.storage.raw_matches[file_name] = raw_matches
                self.storage.save_raw_matches()

    def load_from_storage(self, stored_textobject):
        self.files = stored_textobject['files']
        self.absolute_files = stored_textobject['absolute_files']
        self.is_ebook = stored_textobject['is_ebook']

    def load_from_path(self, path):
        path = Path(path)
        self.is_ebook = False
        self.files = []
        self.absolute_files = []

        if path.suffix == '.epub':
            self.absolute_files = [path.resolve()]
            self.files = self.read_ebook()
            self.is_ebook = True
        elif path.is_file():
            self.files = [path.name]
            self.absolute_files = [path.resolve()]
        elif path.is_dir():
            files = [f for f in path.iterdir() if f.is_file()]
            self.files, self.absolute_files = zip(*[(f.name, f.resolve()) for f in files])

    def update_storage(self):
        self.storage.metadata['TextObject'] = {
            'files' : self.files,
            'absolute_files' : [str(f) for f in self.absolute_files],
            'is_ebook': self.is_ebook,
        }

        self.storage.save_metadata()

    def get_file_content(self, file_name):
        if self.is_ebook:
            content = self.read_epub_file(file_name)
        else:
            content = self.read_system_file(file_name)

        if os.path.splitext(file_name)[1] == '.html':
            content = self.parse_text_from_html(content)

        return content

    def read_system_file(self, file_name):
        for i, other_file_name in self.files:
            if other_file_name == file_name:
                return Path(self.absolute_files[i]).read_text()

    def read_epub_file(self, file_name):
        book = self.get_ebook()
        for item in book.get_items():
            if item.file_name == file_name:
                file = item
                break

        return item.get_body_content()

    def get_ebook(self):
        import ebooklib
        from ebooklib import epub
        return epub.read_epub(self.absolute_files[0])

    def read_ebook(self):
        import ebooklib
        book = self.get_ebook()

        files = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                files.append(item.file_name)

        return files

    def parse_text_from_html(self, content):
        from bs4 import BeautifulSoup
        return "".join(BeautifulSoup(content).findAll(text=True))
