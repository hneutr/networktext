"""
holds methods for entities
- cleaning their strings
- formatting them for storage
- getting them for a given file
    - or all files
"""
import os
import hashlib
from collections import defaultdict

class TextEntities():
    """centralized place for handling of entities, aliases, blacklist, etcetera."""
    def __init__(self, storage):
        self.storage = storage
        self.blacklist = self.load_blacklist()
        self.entities = self.load_entities()
        self.aliases = self.load_aliases(self.entities)

    def load_blacklist(self):
        """loads the blacklist"""
        with open(self.storage.get_loc('blacklist'), 'r') as f:
            blacklist = [l.strip() for l in f.readlines()]

        return blacklist

    def load_entities(self):
        """loads the aliases"""
        with open(self.storage.get_loc('entities'), 'r') as f:
            entities = [Entity.load_from_storage(l.strip()) for l in f.readlines()]

        return entities

    def load_aliases(self, entities):
        """loads the aliases"""
        with open(self.storage.get_loc('aliases'), 'r') as f:
            aliases = [Alias.load_from_storage(l.strip(), entities) for l in f.readlines()]

        return aliases

    @classmethod
    def find_entity_with_key(cls, entities, key):
        """finds an entity that matches the given key. keys are assummed to be
        unique, so just returns the first one"""
        for entity in entities:
            if entity == key:
                return entity

        return None

    @classmethod
    def find_alias_with_key(cls, aliases, key):
        """finds an alias that matches the given key. keys are assummed to be
        unique, so just returns the first one"""
        for alias in aliases:
            if alias == key:
                return alias

        return None

    def update_storage(self):
        """updates the state of the storage"""
        blacklist_content = self.blacklist_file_contents
        with open(self.storage.get_loc('blacklist'), 'w') as f:
            f.write(blacklist_content)

        entities_content = self.entities_file_contents
        with open(self.storage.get_loc('entities'), 'w') as f:
            f.write(entities_content)

        aliases_content = self.aliases_file_contents
        with open(self.storage.get_loc('aliases'), 'w') as f:
            f.write(aliases_content)

        self.storage.metadata['blacklist_hash'] = self.get_content_hash(blacklist_content)
        self.storage.metadata['entities_hash'] = self.get_content_hash(entities_content)
        self.storage.metadata['aliases_hash'] = self.get_content_hash(aliases_content)
        self.storage.save_metadata()

    @property
    def matches_are_not_up_to_date(self):
        old_new_hash_pairs = [
            (
                self.get_content_hash(self.blacklist_file_contents), 
                self.storage.metadata.get('blacklist_hash'),
            ),
            (
                self.get_content_hash(self.entities_file_contents),
                self.storage.metadata.get('entities_hash', None),
            ),
            (
                self.get_content_hash(self.aliases_file_contents),
                self.storage.metadata.get('aliases_hash', None),
            ),
        ]

        for old, new in old_new_hash_pairs:
            if old != new:
                return True

        return False

    def get_content_hash(self, content=''):
        return hashlib.sha224(content.encode('utf-8')).hexdigest()

    @property
    def blacklist_file_contents(self):
        return os.linesep.join(sorted([b for b in self.blacklist]))

    @property
    def entities_file_contents(self):
        return os.linesep.join(
            sorted([e.get_storage_representation() for e in self.entities])
        )

    @property
    def aliases_file_contents(self):
        return os.linesep.join(
            sorted([a.get_storage_representation() for a in self.aliases])
        )

    def unlabeled_entities(self, matches):
        """returns the unlabeled entities
        start from clean matches
        - remove entities
        - remove blacklist
        - remove aliases
        """
        clean_matches = [m.clean_text for m in matches]
        unlabeled_entities = {m for m in clean_matches if m}.difference(
            {e.key for e in self.entities}
        ).difference(
            {b for b in self.blacklist}
        ).difference(
            {a.string for a in self.aliases}
        )

        return list(unlabeled_entities)

    def add_entity_keys_to_matches(self, raw_matches, include_unlabeled=False):
        """returns entities in a given section
        takes all of the matches and finds their entity (disambiguating aliases)
        if include_unlabeled is True, don't require an entity/alias
        """
        matches = []
        for match in raw_matches:
            clean_text = match.clean_text

            if clean_text in self.blacklist:
                continue

            entity = self.find_entity_with_key(self.entities, clean_text)

            found_entity_or_alias = False

            if entity:
                match.key = entity.key
                found_entity_or_alias = True
            else:
                alias = self.find_alias_with_key(self.aliases, clean_text)

                if alias:
                    match.key = alias.entity.key
                    found_entity_or_alias = True

            if found_entity_or_alias or include_unlabeled:
                matches.append(match)

        return matches

    def get_entities_with_aliases(self):
        """gets the entities in a nice format for spacy's matcher"""
        entities_with_aliases = defaultdict(list)

        for entity in self.entities:
            entities_with_aliases[entity.key].append(entity.key)

        for alias in self.aliases:
            entities_with_aliases[alias.entity.key].append(alias.string)

        return entities_with_aliases


class Scope():
    """restricts the scope of something (an alias or entity)."""
    def __init__(self, sections_list):
        self.sections_list = sections_list

    def in_scope(self, section_name, start_token, end_token):
        return True

class Entity():
    """an entity in a text. has a key and a set of aliases."""
    def __init__(self, key):
        self.key = key
        self.aliases = []
        self.scope = None

    def __eq__(self, other):
        """there are two ways we look for equality:
        - if the `other` is an `Entity`, just check that way (i.e., super)
        - if the `other` is a string, check if it is equal to this entity's key
        """
        if isinstance(other, Entity):
            return super(Entity, self).__eq__(other)
        elif isinstance(other, str):
            return self.key == other
        else:
            return False

    def get_storage_representation(self):
        """should probably later be able to set scopes"""
        return '"{key}"'.format(key=self.key)

    @classmethod
    def load_from_storage(cls, line):
        """given a line of a file, returns an entity for that line
        handles entities with scopes and without (all lack scopes for now)"""
        key = line.split(',', 1)[0].strip('"')
        return Entity(key=key)

    def __repr__(self):
        if bool(self.aliases):
            representation = '{key}:\n{aliases}'.format(
                key=self.key,
                aliases="\n".join(["\t" + a.string for a in self.aliases])
            )
        else:
            representation = '{key}'.format(key=self.key)

        return representation

class Alias():
    """an alias of an entity.
    can have a scope
    """
    def __init__(self, string, entity, scope=None):
        self.string = string
        self.entity = entity
        self.scope = scope

    def __eq__(self, other):
        """there are two ways we look for equality:
        - if the `other` is an `Alias`, just check that way (i.e., super)
        - if the `other` is a string, check if it is equal to this alias's key
        """
        if isinstance(other, Alias):
            return super(Alias, self).__eq__(other)
        elif isinstance(other, str):
            return self.string== other
        else:
            return False

    def get_storage_representation(self):
        """represented as: "ENTITY_KEY","ALIAS_STRING","SCOPE"
        should probably later be able to set scopes"""
        return '"{key}","{alias_string}"'.format(key=self.entity.key, alias_string=self.string)

    @classmethod
    def load_from_storage(cls, line, entities):
        """given a line of a file, returns an alias for that line
        handles entities with scopes and without (all lack scopes for now)"""
        entity_key, alias_string = [part.strip('"') for part in line.split('","')]
        entity = TextEntities.find_entity_with_key(entities, entity_key)
        return Alias(string=alias_string, entity=entity)

    def __repr__(self):
        return "{string} ({entity_key})".format(string=self.string, entity_key=self.entity.key)

