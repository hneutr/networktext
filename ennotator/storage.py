import json
import os
from pathlib import Path

class Datastore():
    def __init__(self, path):
        self.path = path

        if not os.path.isdir(path):
            os.mkdir(path)

    def get_loc(self, path):
        return os.path.join(self.path, path)

class TextDatastore():
    files = [
        "entities",
        "blacklist",
        "aliases",
        "attributes",
        "matches",
    ]

    def __init__(self, text_name, datastore_path='.ennotator_data'):
        self.text_name = text_name
        if not datastore_path:
            datastore_path = '.ennotator_data'
        self.datastore = Datastore(os.path.join(os.getcwd(), datastore_path))

        # sanitize the text's name to use as a path
        safe_text_path = "".join(_ for _ in self.text_name if _.isalnum())

        self.datastore_path = self.datastore.get_loc(safe_text_path)

        self.ready()


    def ready(self):
        """if the dataset exists, loads it
        otherwise, sets things up so we can work safely"""
        if not os.path.exists(self.datastore_path) or not os.path.isdir(self.datastore_path):
            os.mkdir(self.datastore_path)

        if not os.path.isfile(self.metadata_path):
            self.metadata = {
                'text_name' : self.text_name,
                'datastore_path' : self.datastore_path,
                'file_match_hashes' : {},
                'files' : {
                    'ordering' : [],
                    'exclusions' : [],
                }
            }

            self.save_metadata()

        if not os.path.isfile(self.raw_entities_path):
            self.raw_entities = {}
            self.save_raw_entities()

        for file in TextDatastore.files:
            Path(self.get_loc(file)).touch()

        self.load_metadata()
        self.load_raw_entities()


    def get_file_content(self, file):
        with open(self.get_loc(file), 'r') as f:
            content = f.read()

        return content

    def save_file_content(self, file, content):
        with open(self.get_loc(file), 'w') as f:
            f.write(content)

    @property
    def raw_entities_path(self):
        return self.get_loc('raw_entities')

    @property
    def metadata_path(self):
        return self.get_loc('metadata')

    def save_raw_entities(self):
        with open(self.raw_entities_path, 'w') as f:
            json.dump(self.raw_entities, f)

    def save_metadata(self):
        """
        fields:
        - text_name: string, name of text
        - datastore_path: path to datastore (where this file is, lol)
        - file_match_hashes: dict. filename to hash of contents.
        """
        print('TODO: use hashes')
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f)

    def load_metadata(self):
        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)

    def load_raw_entities(self):
        from . matcher import Match
        with open(self.raw_entities_path, 'r') as f:
            raw_entities = json.load(f)

        self.raw_entities = {}
        for file_name, file_raw_entities in raw_entities.items():
            self.raw_entities[file_name] = [Match(start=m['start'], end=m['end'], text=m['text']) for m in file_raw_entities]

    def get_loc(self, path):
        return os.path.join(self.datastore_path, path)
