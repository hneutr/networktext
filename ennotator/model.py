"""
cache spacy
@author: Carl Mueller
"""
from functools import partial
from cachetools import cached, Cache
from cachetools.keys import hashkey
import spacy

@cached(Cache(1), key=partial(hashkey, 'spacy'))
def load_spacy(model_name, **kwargs):
    """
    Load a language-specific spaCy pipeline (collection of data, models, and
    resources) for tokenizing, tagging, parsing, etc. text; the most recent
    package loaded is cached.
    Args:
        name (str): standard 2-letter language abbreviation for a language;
            currently, spaCy supports English ('en') and German ('de')
        **kwargs: keyword arguments passed to :func:`spacy.load`; see the
            `spaCy docs <https://spacy.utils/docs#english>`_ for details
            * via (str): non-default directory from which to load package data
            * vocab
            * tokenizer
            * parser
            * tagger
            * entity
            * matcher
            * serializer
            * vectors
    Returns:
        :class:`spacy.<lang>.<Language>`
    Raises:
        RuntimeError: if package can't be loaded
    """
    print("Loading Spacy model into cache...")
    return spacy.load(model_name, **kwargs)
