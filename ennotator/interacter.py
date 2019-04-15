import copy
import json

from . import entities

class Interacter():
    def handle_input(self, input_string):
        1

    def update_storage(self): 
        pass

    def interaction(self, function):
        """wraps an interactive function in a call to update the storage"""
        def wrapper(self):
            function()
            self.update_storage()

        return wrapper(self)


    def list_interaction(self, _list, prompt_string):
        sorted_list = sorted(copy.deepcopy(_list))
        print("enter i) the # of the {prompt_string} or ii) `z` to quit.".format(prompt_string=prompt_string))
        for i, x in enumerate(sorted_list):
            print("[{i}] - {x}".format(i=i+1, x=x))

        answer = input().strip()

        element_index = None
        should_quit = False

        if answer.isdigit():
            index = int(answer) - 1

            if index < len(_list):
                # because we sorted, we gotta convert the index
                element_index = _list.index(sorted_list[index])
            else:
                print("no option {}.".format(index))
        elif answer == 'z':
            should_quit = True

        return element_index, should_quit

class FileInteracter(Interacter):
    def __init__(self, storage, files, ordering=[], exclusions=[]):
        self.storage = storage
        self.files = files
        self.ordering = ordering
        self.exclusions = exclusions
        1

    def update_storage(self):
        self.storage.metadata['files']['exclusions'] = self.exclusions
        self.storage.metadata['files']['ordering'] = self.ordering
        self.storage.save_metadata()

    def order(self):
        """order is kinda dumb, you can only add things to the end"""
        should_quit = False
        unordered_files = self.files
        unordered_files = [f for f in unordered_files if f not in self.ordering]
        unordered_files = [f for f in unordered_files if f not in self.exclusions]
        unordered_files = sorted(unordered_files)

        while not should_quit and len(unordered_files) != len(self.files):
            index_to_order, should_quit = self.list_interaction(
                unordered_files,
                "the file to add to the ordering",
            )

            if index_to_order is not None:
                element = unordered_files.pop(index_to_order)
                self.ordering.append(element)
                print("'{}' added to order.".format(index_to_order))

        self.update_storage()

    def unorder(self):
        """unorder is kinda dumb, you can remove things from the order"""
        should_quit = False
        while not should_quit and len(self.ordering):
            index_to_unorder, should_quit = self.list_interaction(
                self.ordering,
                "the file to unorder",
            )

            if index_to_unorder != None:
                element = self.ordering.pop(index_to_unorder)
                print("'{}' unordered.".format(element))

        self.update_storage()

    def exclude(self):
        should_quit = False
        while not should_quit and len(self.exclusions) < len(self.files):
            unexcluded_files = [f for f in self.files if f not in self.exclusions]

            index_to_exclude, should_quit = self.list_interaction(
                unexcluded_files,
                "the file to exclude",
            )

            if index_to_exclude != None:
                element = unexcluded_files[index_to_exclude]
                self.exclusions.append(element)

                if element in self.ordering: self.ordering.remove(element)

                print("'{}' excluded.".format(element))

        self.update_storage()

    def unexclude(self):
        should_quit = False
        while not should_quit and len(self.exclusions):
            index_to_unexclude, should_quit = self.list_interaction(
                self.exclusions,
                "the file to unexclude",
            )

            if index_to_unexclude != None:
                element = self.exclusions.pop(index_to_unexclude)
                print("'{}' unexcluded.".format(element))

        self.update_storage()

class EntityInteracter(Interacter):
    def __init__(self, entity_interface):
        self.entity_interface = entity_interface

        # ENTITIES will be one entity per line
        # STRINGS_BLACKLIST will be one string per line
        # ALIASES will be one per line:
        #   - "entity", "alias", INCLUDE_IN_FILES:[],EXCLUDE_FROM_FILES:[]

    def label_entities(self):
        unlabeled_entities = sorted(self.entity_interface.unlabeled_entities)

        print(self.entity_interface.entities)
        count_of_unlabeled_entities = len(unlabeled_entities)
        for i, unlabeled_entity in enumerate(unlabeled_entities):
            handler = self.list_interaction(
                [e.key for e in self.entity_interface.entities],
                [
                    NewEntityListInteractionHandler(print_precedence=0),
                    ExistingEntityListInteractionHandler(print_precedence=1),
                    NotEntityListInteractionHandler(print_precedence=2),
                    SkipEntityListInteractionHandler(print_precedence=3),
                    QuitListInteractionHandler(print_precedence=4),
                ],
                prompt="match {i}/{total}: {unlabeled_entity}".format(
                    i=i,
                    total=count_of_unlabeled_entities,
                    unlabeled_entity=unlabeled_entity,
                )
            )

            if handler.name == 'not_entity':
                self.entity_interface.blacklist.append(unlabeled_entity)
            elif handler.name == 'new_entity':
                entity = entities.Entity(key=handler.result)
                self.entity_interface.entities.append(entity)
                # add an alias if the key is different from the unlabeled entity
                # supplied
                if handler.result != unlabeled_entity:
                    alias = entities.Alias(string=unlabeled_entity, entity=entity)
                    self.entity_interface.aliases.append(alias)
            elif handler.name == 'existing_entity':
                entity_index = handler.result
                entity = self.entity_interface.entities[entity_index]
                alias = entities.Alias(string=unlabeled_entity, entity=entity)
                self.entity_interface.aliases.append(alias)
            elif handler.name == 'quit':
                break

            self.entity_interface.update_storage()

    def list_interaction(self, _list, handlers, prompt=""):
        sorted_list = sorted(copy.deepcopy(_list))
        handlers_in_order_to_print = sorted(handlers, key=lambda h: h.print_precedence)

        print_string = "type \n"
        for i, handler in enumerate(handlers_in_order_to_print):
            print_string += "{index}) {string}\n".format(index=i + 1, string=handler.description)

        print(print_string)

        for i, option in enumerate(sorted_list):
            print("[{i}] - {option}".format(i=i+1, option=option))

        print(prompt)

        answer = input().strip()

        # order the handlers by restrictiveness so no false positives occur
        for abstract_handler in handler_restrictivenesses():
            for handler in handlers:
                if isinstance(handler, abstract_handler):
                    if handler.meets_conditions(answer):
                        handler.set_result(answer, _list, sorted_list)
                        return handler

        # main interactions are adds:
        # - add an entity
        # - add an entity alias
        # - add to blacklist

        # how to do ^:
        # - add an entity: type string
        # - add an entity alias: enter the index of the entity
        # - add to blacklist: type 0


        # later:
        # - change an entity key

        # removes:
        # - remove an entity
        # - remove an entity alias
        # - remove from blacklist


        ################################################################################
        # ENTITY SCOPING
        ################################################################################
        # - add file to entity exclusion
        # - add file to entity inclusion
        # - remove file from entity exclusion
        # - remove file from entity inclusion
        # - remove entity inclusions (aka default to always include)

def handler_restrictivenesses():
    """these handlers have different restrictiveness (of course) and need
    to be 'asked' in a given order from most restrictive to least so as to
    not get false positives
    """
    return [
        SkipEntityListInteractionHandler,
        ExistingEntityListInteractionHandler,
        QuitListInteractionHandler,
        NewEntityListInteractionHandler,
        NotEntityListInteractionHandler,
    ]

class ListInteractionHandler():
    """abstract method for list interaction handlers."""
    name = ''
    description = ''

    def __init__(self, print_precedence=0):
        self.print_precedence = print_precedence
        self.result = None

    @staticmethod
    def meets_conditions(answer):
        """returns true if the list interaction should be handled by this method"""
        return bool(answer)

    def set_result(self, answer, _list, sorted_list):
        """returns the result of this handler.
        given:
        - the list of options
        - the sorted list of options
        - the user's answer
        """
        self.result = answer

class QuitListInteractionHandler(ListInteractionHandler):
    """quits"""
    name = 'quit'
    description = '`z` to quit.'

    @staticmethod
    def meets_conditions(answer):
        return bool(answer == 'z')

class NotEntityListInteractionHandler(ListInteractionHandler):
    """indicates this is not an entity"""
    name = 'not_entity'
    description = 'enter to indicate this is not an entity'

    @staticmethod
    def meets_conditions(answer):
        return not bool(answer)

class ExistingEntityListInteractionHandler(ListInteractionHandler):
    """adds an alias to an entity"""
    name = 'existing_entity'
    description = 'the # of the the entity this is an alias of'

    @staticmethod
    def meets_conditions(answer):
        return answer.isdigit()

    def set_result(self, answer, _list, sorted_list):
        index = int(answer) - 1
        print('THIS IS NOT WORKING')
        self.result = _list.index(sorted_list[index])

class NewEntityListInteractionHandler(ListInteractionHandler):
    """adds a new entity"""
    name = 'new_entity'
    description = 'a string to add a new entity'

    @staticmethod
    def meets_conditions(answer):
        return bool(answer)

class SkipEntityListInteractionHandler(ListInteractionHandler):
    """skips an entity"""
    name = 'skip_entity'
    description = '0 to skip labeling this entity'

    @staticmethod
    def meets_conditions(answer):
        return answer.isdigit() and int(answer) == 0

    def set_result(self, answer, _list, sorted_list):
        self.result = int(answer)
