import re
from spacy.matcher import Matcher as SpacyMatcher
from collections import defaultdict

from . import model
from . import entities

def make_stopwords():
    """turns things into stopwords, yaknow"""
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

class EntityMatchObject():
    """interfaces with spacy to make entity recognition better based on
    user-supplied entities and disambiguations"""
    def __init__(self, entities_with_aliases={}):
        self.entities_with_aliases = entities_with_aliases

    @property
    def nlp(self):
        return model.load_spacy('en_core_web_md')

    @property
    def matcher(self):
        self._matcher = SpacyMatcher(self.nlp.vocab)

        for key, aliases in self.entities_with_aliases.items():
            patterns = []
            for alias in aliases:
                patterns.append([{'ORTH' : part} for part in alias.split()])

            self._matcher.add(key, None, *patterns)

        return self._matcher

    def get_matches(self, text):
        doc = self.nlp(text)
        matches = []

        seen_matches = defaultdict(defaultdict(defaultdict(dict).copy).copy)
        matcher = self.matcher
        raw_matches = matcher(doc)

        for _id, start, end in raw_matches:
            text = doc[start:end].text
            key = matcher.vocab.strings[_id]
            matches.append(Match(start=start, end=end, text=text, key=key))
            seen_matches[start][end][text] = True

        for match in [e for e in doc.ents if e.label_ == 'PERSON']:
            start = match.start_char
            end = match.end_char
            text = match.text

            if not seen_matches[start][end][text]:
                matches.append(Match(
                    text=text,
                    start=start,
                    end=end,
                ))

        return matches

class Match(dict):
    def __init__(self, start=0, end=0, text="", key=None):
        # init a dict so we can json.dump this
        dict.__init__(self, start=start, end=end, text=text, key=key)

        self.start = start
        self.end = end
        self.text = text

        # we will overwrite this later if this has an entity/alias associated
        # with it
        self.key = key if key else text

    def __str__(self):
        if self.key == self.text:
            return "'{}': {}, {}".format(self.text, self.start, self.end)
        else:
            return "'{} ({})': {}, {}".format(self.text, self.key, self.start, self.end)

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

STOPWORDS = make_stopwords()
