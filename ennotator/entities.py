"""
holds methods for entities
- cleaning their strings
- formatting them for storage
- getting them for a given file
    - or all files
"""
import copy
import json
import os

from . import matcher

class TextEntities():
    """centralized place for handling of entities, aliases, blacklist, etcetera."""
    def __init__(self, storage, reader):
        self.storage = storage
        self.reader = reader
        self.blacklist = self.load_blacklist()
        self.entities = self.load_entities()
        self.aliases = self.load_aliases(self.entities)
        self.matches_by_section = self.load_matches_by_section()
        self.all_matches = [m for matches in self.matches_by_section.values() for m in matches]

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

    def load_matches_by_section(self):
        """this function calls one that is poorly named (raw_entities; they're matches)"""
        matches_by_section = dict()
        for file_name in self.reader.ordered_content_files:
            matches_by_section[file_name] = self.storage.raw_entities[file_name]

        return matches_by_section

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
        with open(self.storage.get_loc('blacklist'), 'w') as f:
            for b in self.blacklist:
                f.write(b + os.linesep)

        entities_content = [e.get_storage_representation() for e in self.entities]
        with open(self.storage.get_loc('entities'), 'w') as f:
            for l in entities_content:
                f.write(l + os.linesep)

        aliases_content = [a.get_storage_representation() for a in self.aliases]
        with open(self.storage.get_loc('aliases'), 'w') as f:
            for l in aliases_content:
                f.write(l + os.linesep)

    @property
    def unlabeled_entities(self):
        """returns the unlabeled entities
        start from clean matches
        - remove entities
        - remove blacklist
        - remove aliases
        """
        clean_matches = [m.clean_text for m in self.all_matches]
        unlabeled_entities = {m for m in clean_matches if m}.difference(
            {e.key for e in self.entities}
        ).difference(
            {b for b in self.blacklist}
        ).difference(
            {a.string for a in self.aliases}
        )

        return list(unlabeled_entities)

    def section_matches_with_entity_keys(self, section_name, include_unlabeled=False):
        """returns entities in a given section
        takes all of the matches and finds their entity (disambiguating aliases)
        if include_unlabeled is True, don't require an entity/alias
        """
        matches = []
        for match in self.matches_by_section[section_name]:
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

