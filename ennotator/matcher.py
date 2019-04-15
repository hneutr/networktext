import re
import spacy.matcher
from collections import defaultdict

from . import model

def make_stopwords():
    from spacy.lang.en import stop_words
    stop_words = stop_words.STOP_WORDS
    contractions = ["n't", "'d", "'ll", "'m", "'re", "'s", "'ve"]

    contraction_stopwords = list()
    for apostrophe in ["'", "‘", "’"]:
        for contraction in contractions:
            for stop_word in stop_words:
                contraction_stopwords.append(stop_word + contraction.replace("'", apostrophe))

    stop_words.update(contraction_stopwords)
    return stop_words

class Match(dict):
    def __init__(self, start=0, end=0, text=""):
        # init a dict so we can json.dump this
        dict.__init__(self, start=start, end=end, text=text)

        self.start = start
        self.end = end
        self.text = text

        # we will overwrite this later if this has an entity/alias associated
        # with it
        self.key = text

    def __str__(self):
        return "'{}': {}, {}".format(self.text, self.start, self.end)

    def __lt__(self, other):
        return self.text < other.text

    @property
    def clean_text(self):
        text = self.text.strip()
        text = text.replace('\n', ' ')

        # remove non-alphabetical characters from either side of the string
        text = self.strip_nonalphabetical_chars_from_sides_of_string(text)
        text = " ".join(text.split())

        if text.lower() in STOPWORDS:
            return None

        if len([c for c in text if c.isalpha()]) > 1:
            return text

    @classmethod
    def strip_nonalphabetical_chars_from_sides_of_string(cls, string):
        """strips nonalphabetical characters from the left and right of the string."""
        # left side
        for i, c in enumerate(string):
            if c.isalpha():
                string = string[i:]
                break

        # reverse the string
        string = string[::-1]

        # right side
        for i, c in enumerate(string):
            if c.isalpha():
                string = string[i:]
                break

        return string[::-1]


class EnnotatorMatcher():
    def __init__(self, text, entities=[], blacklist=[]):
        """
        params: 
        - text: text to match
        - entities: list of tuples (id, alias)
        - blacklist: list of strings
        """
        self.nlp = model.load_spacy('en_core_web_md')
        self.document = self.nlp(text)
        self.blacklist = blacklist

    def get_raw_entities(self):
        entities = []
        for entity in [e for e in self.document.ents if e.label_ == 'PERSON']:
            entities.append(Match(
                text=entity.text,
                start=entity.start_char,
                end=entity.end_char,
            ))

        return entities

STOPWORDS = make_stopwords()
