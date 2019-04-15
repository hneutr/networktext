from . import entities
from . import interacter
from . import matcher
from . import network
from . import reader
from . import storage

# the default process of doing this is:
# 1. load the data
# 2. save it
# 3. match on it
# 4. make entities from it
#   - psueonyms
#   - blacklists
#   - etc

class Ennotator():
    def __init__(self, text_name, path, datastore_path=None, reload_entities=False):
        self.storage = storage.TextDatastore(text_name, datastore_path)
        self.entity_interface = entities.TextEntities(self.storage)
        self.reader = reader.TextReader(self.storage, path)

        if self.entity_interface.matches_are_not_up_to_date:
            entities_with_aliases = self.entity_interface.get_entities_with_aliases()
            self.reader.load_matches(reload=True, entities_with_aliases=entities_with_aliases)

        self.network = network.TextNetwork(
            self.storage,
            self.reader.ordered_content_files,
            self.entity_interface,
        )

        self.interacter = {
            'files' : interacter.FileInteracter(
                self.storage,
                self.reader.files,
                self.storage.metadata['files']['ordering'],
                self.storage.metadata['files']['exclusions'],
            ),
            'entities' : interacter.EntityInteracter(
                self.storage,
                self.entity_interface,
            ),
        }
