"""
We need paragraph regions before we can do quote tagging::

    >>> from .chapter import tagger_chapter
    >>> from .metadata import tagger_metadata

quote.quote / quote.nonquote regions
------------------------------------

Quotes are discovered by parsing text using unicode word boundary rules. If a
word is found that matches the list of quote marks, then a quote is formed when
the corresponding close quote mark is found::

    >>> [x for x in run_tagger('''
    ... “Thou find’st it out, child?  Ay, ’tis worth all the feather-beds and\r
    ... pouncet-boxes in Ulm; is it not?  That accursed Italian fever never left
    ... me till I came up here.  A man can scarce draw breath in your foggy
    ... meadows below there.  Now then, ‘here is the view open.’  What think you of
    ... the Eagle’s Nest?”
    ...
    ... ‘And this is Schloss Adlerstein?’ she exclaimed.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 305, None, '“Thou find’st it out...f\\nthe Eagle’s Nest?”'),
     ('quote.quote', 307, 340, None, '‘And this is Schloss Adlerstein?’'),
     ('quote.nonquote', 341, 355, None, 'she exclaimed.')]

Quotes should either be at least 5 words long::

    >>> [x for x in run_tagger('''
    ... The "exotic camels" were actually dromedaries.
    ... "Four words not quote" "Five words is a quote"
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.nonquote', 0, 69, None, 'The "exotic camels" ...our words not quote"'),
     ('quote.quote', 70, 93, None, '"Five words is a quote"')]

... or have one of ``,?.!-;_`` before the end quote, or ``--`` after::

    >>> [x for x in run_tagger('''
    ... "That," he said, "is a 'veritable banquet'."
    ...
    ... "Because"--"because father and mamma have to go away," I was going to say
    ...
    ... "Here's luck," "A fair wind," and "Billy Bones his fancy," were very neatly
    ... and clearly executed on the forearm.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 7, None, '"That,"'),
     ('quote.nonquote', 8, 16, None, 'he said,'),
     ('quote.quote', 17, 44, None, '"is a \\'veritable banquet\\'."'),
     ('quote.quote', 46, 55, None, '"Because"'),
     ('quote.nonquote', 55, 57, None, '--'),
     ('quote.quote', 57, 100, None, '"because father and ...ma have to go away,"'),
     ('quote.nonquote', 101, 119, None, 'I was going to say'),
     ('quote.quote', 121, 135, None, '"Here\\'s luck,"'),
     ('quote.quote', 136, 150, None, '"A fair wind,"'),
     ('quote.nonquote', 151, 154, None, 'and'),
     ('quote.quote', 155, 179, None, '"Billy Bones his fancy,"'),
     ('quote.nonquote', 180, 233, None, 'were very neatly\\nand...uted on the forearm.')]

Plural possessives are explicitly not counted as quotes::

    >>> [x for x in run_tagger('''
    ... or two, which he had always lost after a few days’ friendship, felt as if
    ... always very near at hand.
    ...
    ... After a few days' friendship, he said 'can I borrow your lawnmower?'
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.nonquote', 0, 99, None, 'or two, which he had...s very near at hand.'),
     ('quote.nonquote', 101, 138, None, "After a few days' friendship, he said"),
     ('quote.quote', 139, 169, None, "'can I borrow your lawnmower?'")]

Quotes that spread across paragraphs are broken into separate paragraph chunks::

    >>> [x for x in run_tagger('''
    ... “Oh, that’s not all that complicated,” J.R. answered. “If you closed
    ... quotes at the end of every paragraph, then you would need to reidentify the
    ... speaker with every subsequent paragraph.
    ...
    ... “Say a narrative was describing two or three people engaged in a lengthy
    ... conversation. If you closed the quotation marks in the previous paragraph,
    ... reader knows that the previous speaker is still the one talking.”
    ...
    ... “Oh, that makes sense. Thanks!”
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 38, None, '“Oh, that’s not all that complicated,”'),
     ('quote.nonquote', 39, 53, None, 'J.R. answered.'),
     ('quote.quote', 54, 185, None, '“If you closed\\nquote...ubsequent paragraph.'),
     ('quote.quote', 187, 400, None, '“Say a narrative was...ll the one talking.”'),
     ('quote.quote', 402, 433, None, '“Oh, that makes sense. Thanks!”')]

Non-quote regions don't run outside chapters, so Titles aren't part of them::

    >>> [x for x in run_tagger('''
    ... The Wind in the Willows
    ... Kenneth Grahame
    ...
    ... CHAPTER I. THE RIVER BANK
    ...
    ... The Mole had been working very hard all the morning, spring-cleaning.
    ... ‘Hold up!’ said an elderly rabbit at the gap. ‘Sixpence for the
    ... privilege of passing by the private road!’
    ...
    ... CHAPTER IV. MR. BADGER
    ...
    ... ‘Thought I should find you here all right,’ said the Otter cheerfully.
    ...
    ... ‘They were all in a great state of alarm along River Bank when I arrived
    ... this morning.’
    ... '''.strip(), tagger_metadata, tagger_chapter, tagger_quote) if x[0] in set(('metadata.title', 'metadata.author', 'quote.quote', 'quote.nonquote'))]
    [('metadata.title', 0, 23, None, 'The Wind in the Willows'),
     ('metadata.author', 24, 39, None, 'Kenneth Grahame'),
     ('quote.nonquote', 68, 137, None, 'The Mole had been wo...ng, spring-cleaning.'),
     ('quote.quote', 138, 148, None, '‘Hold up!’'),
     ('quote.nonquote', 149, 183, None, 'said an elderly rabbit at the gap.'),
     ('quote.quote', 184, 244, None, '‘Sixpence for the\\npr...y the private road!’'),
     ('quote.quote', 270, 313, None, '‘Thought I should fi...you here all right,’'),
     ('quote.nonquote', 314, 340, None, 'said the Otter cheerfully.'),
     ('quote.quote', 342, 429, None, '‘They were all in a ...rived\\nthis morning.’')]

quote.suspension regions
------------------------

A suspension is defined as a ``quote.nonquote`` that is not bordered by the end or start
of a sentence. If it is longer than 5 words, then it is a long suspension. For example::

    >>> [x for x in run_tagger('''
    ... “And on what evidence, Pip,” asked Mr. Jaggers, very coolly, as he
    ... paused with his handkerchief half way to his nose, “does Provis make this
    ... claim?”
    ...
    ... “He does not make it,” said I, “and has never made it, and has no knowledge
    ... or belief that his daughter is in existence.”
    ...
    ... ‘And this is Schloss Adlerstein?’ she exclaimed.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0].startswith('quote.')]
    [('quote.quote', 0, 28, None, '“And on what evidence, Pip,”'),
     ('quote.nonquote', 29, 117, None, 'asked Mr. Jaggers, v...alf way to his nose,'),
     ('quote.suspension.long', 29, 117, None, 'asked Mr. Jaggers, v...alf way to his nose,'),
     ('quote.quote', 118, 148, None, '“does Provis make this\\nclaim?”'),
     ('quote.quote', 150, 172, None, '“He does not make it,”'),
     ('quote.nonquote', 173, 180, None, 'said I,'),
     ('quote.suspension.short', 173, 180, None, 'said I,'),
     ('quote.quote', 181, 271, None, '“and has never made ...er is in existence.”'),
     ('quote.quote', 273, 306, None, '‘And this is Schloss Adlerstein?’'),
     ('quote.nonquote', 307, 321, None, 'she exclaimed.')]

This example doesn't count, since it starts with a sentence::

    >>> [x for x in run_tagger('''
    ... Little Benjamin said: "It spoils people's clothes to squeeze under a gate;
    ... the proper way to get in is to climb down a pear-tree."
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0].startswith('quote.')]
    [('quote.nonquote', 0, 21, None, 'Little Benjamin said:'),
     ('quote.quote', 22, 130, None, '"It spoils people\\'s ...b down a pear-tree."')]

.. http://unicode.org/reports/tr29/#Word_Boundaries
"""
import re

import icu

from ..icuconfig import DEFAULT_LOCALE
from .utils import region_append_without_whitespace, regions_invert


QUOTES = {
    '“': '”',  # English double.
    '‘': '’',  # English Single.
    '"': '"',  # Double universal.
    "'": "'",  # Single universal.
}


def tagger_quote_quote(book):
    """Add quote.quote tags to (book)"""
    if len(book.get('quote.quote', [])) > 0:
        return  # Nothing to do

    # Create a word iterator for this book
    bi = icu.BreakIterator.createWordInstance(DEFAULT_LOCALE)
    bi.setText(book['content'])

    book['quote.quote'] = []
    for containing_r in book['chapter.paragraph']:
        last_b = containing_r[0]
        open_quote = None
        quote_word_count = 0

        # Get all word breaks after containing_r[0]
        bi.following(containing_r[0] - 1)
        for b in bi:
            if b > containing_r[1]:
                # Outside the chapter now, so stop
                if open_quote:
                    region_append_without_whitespace(book, 'quote.quote', open_quote[1], b)
                break
            word = book['content'][last_b:b]

            if open_quote and word == open_quote[0]:
                # Found the closing quote we were looking for
                r = (open_quote[1], b)
                # Quotes should have either...
                if quote_word_count >= 5:  # ...five or more words
                    book['quote.quote'].append(r)
                elif re.search(r'^\s*--', book['content'][b:b + 5]):  # ...a double-hyphen after it
                    book['quote.quote'].append(r)
                elif re.search(r'--\s*$|[,?.!-;_]$', book['content'][b - 5:b - 1]):  # ...one of several punctuation marks before it
                    book['quote.quote'].append(r)
                open_quote = None
            elif open_quote and bi.getRuleStatus() > 0:
                quote_word_count += 1
            elif not open_quote and word in QUOTES:
                if re.fullmatch(r"s[’']", book['content'][last_b - 1:b]):
                    # Plural posessive, ignore it.
                    pass
                else:
                    # Not in an open quote and found one
                    open_quote = (QUOTES[word], last_b)
                    quote_word_count = 0
            last_b = b


def tagger_quote_nonquote(book):
    """Add quote.nonquote tags to (book)"""
    if len(book.get('quote.nonquote', [])) > 0:
        return  # Nothing to do

    book['quote.nonquote'] = []
    # Combine quotes and everything not in a paragraph
    quotes_and_paras = book['quote.quote'][:]
    quotes_and_paras.extend(regions_invert(book['chapter.paragraph'], len(book['content'])))
    quotes_and_paras.sort(key=lambda r: (r[0], -r[1]))

    # Non-quotes are the opposite of this
    for last_b, b in regions_invert(quotes_and_paras, len(book['content'])):
        region_append_without_whitespace(book, 'quote.nonquote', last_b, b)


def tagger_quote_suspension(book):
    """Add quote.suspension tags to (book)"""
    if len(book.get('quote.suspension.short', [])) > 0 or len(book.get('quote.suspension.long', [])) > 0:
        return  # Nothing to do

    # Iterator that iterates through...
    # (a) The start of the first sentence
    # (b) The end of all sentences (including the first)
    # All other sentence-starts should be just after a sentence-end, so no point
    # considering
    def sentence_breaks_fn():
        if len(book['chapter.sentence']) > 0:
            yield book['chapter.sentence'][0][0]
        for r in book['chapter.sentence']:
            yield r[1]
    sentence_breaks = sentence_breaks_fn()

    # Create a word iterator for this book
    bi = icu.BreakIterator.createWordInstance(DEFAULT_LOCALE)
    bi.setText(book['content'])

    def count_words(f, t):
        out = 0
        bi.following(f - 1)
        for b in bi:
            if b > t:
                break
            if bi.getRuleStatus() > 0:
                out += 1
        return out

    cur_sent_b = -10  # i.e. a value we'll consider before-range
    book['quote.suspension.short'] = []
    book['quote.suspension.long'] = []
    for containing_r in book['quote.nonquote']:
        while cur_sent_b < containing_r[1] + 3:  # while current sentence boundary is before end-of-region
            if cur_sent_b > containing_r[0] - 3:  # If it's after the start-of-region also
                # There is a sentence boundary within this region, ignore and move on
                break
            cur_sent_b = next(sentence_breaks)
        else:
            # Considered all potential sentence boundaries and none found, this is a suspension.
            if count_words(*containing_r) < 5:
                book['quote.suspension.short'].append(containing_r)
            else:
                book['quote.suspension.long'].append(containing_r)


def tagger_quote(book):
    """
    Add quote.* tags to regions
    """
    tagger_quote_quote(book)
    tagger_quote_nonquote(book)
    tagger_quote_suspension(book)
