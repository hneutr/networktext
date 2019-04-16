# networktext

a tool for creating character co-occurrence networks from a text (book, etc).

## what it does now:
- reads text and epub files
- recognizes entities
    - things are cached so they are quick (ish) and only reload when the entities change
- allows for annotations of:
    - entity disambiguation (pseudonyms/aliases)
    - file restriction (i.e., don't include this section of the epub)
    - file ordering (read the network in _this_ way)

this isn't well documented or ordered, nor is it tested

## what it should do in the future:
- support a commandline interface
- allow for scoping of entities
- give you the sentences that an entity occurred in
- be smart about listing entities
    - group them by shared substrings
    - show you the longest first (eg, if there's one character named `Adam Smith` who appears as `Adam` and `Adam Smith`, show `Adam Smith` first)
    - case insensitive?
- auto create the key?
