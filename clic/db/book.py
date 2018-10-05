import psycopg2
import psycopg2.extras

from clic.db.lookup import rclass_id_lookup, api_subset_lookup


def put_book(cur, book):
    """
    Import a book object
    """
    rclass = rclass_id_lookup(cur)

    # Insert book / update content, get ID for other updates
    cur.execute("""
        INSERT INTO book (name, content)
        VALUES (%(name)s, %(content)s)
        ON CONFLICT (name) DO UPDATE SET content=EXCLUDED.content
        RETURNING book_id
    """, dict(
        name=book['name'],
        content=book['content'],
    ))
    (book_id,) = cur.fetchone()

    # Replace tokens with new values
    cur.execute("DELETE FROM token WHERE book_id = %(book_id)s", dict(book_id=book_id))
    psycopg2.extras.execute_values(cur, """
        INSERT INTO token (book_id, crange, ttype, ordering) VALUES %s
    """, ((
        book_id,
        psycopg2.extras.NumericRange(off_start, off_end),
        ttype,
        i,
    ) for i, (rclass_name, ttype, off_start, off_end) in enumerate(book['regions']) if rclass_name == 'token.word'))

    # Replace regions with new values
    cur.execute("DELETE FROM region WHERE book_id = %(book_id)s", dict(book_id=book_id))
    psycopg2.extras.execute_values(cur, """
        INSERT INTO region (book_id, crange, rclass_id, rvalue) VALUES %s
    """, ((
        book_id,
        psycopg2.extras.NumericRange(off_start, off_end),
        rclass[rclass_name],
        rvalue,
    ) for rclass_name, rvalue, off_start, off_end in book['regions'] if rclass_name != 'token.word'))


def get_book(cur, book_id, content=False, tokens=False, regions=False):
    """Get book from DB, specifying what details are required"""
    out = dict(id=book_id)

    # Initial fetch from main table
    cur.execute("SELECT name, " + ("content" if content else "NULL") + " AS content FROM book WHERE book_id = %s", (book_id,))
    (out['name'], out['content'],) = cur.fetchone()
    if not content:
        del out['content']

    if tokens:
        raise NotImplementedError()
    if regions:
        raise NotImplementedError()

    return out


def get_book_metadata(cur, book_ids, metadata):
    """
    Generate dict of metadata that should go in footer of both concordance and subsets
    - book_ids: Array of book IDs to include
    - metadata: Metadata items to include, a set contining some of...
      - 'book_titles': The title / author of each book
      - 'chapter_start': The start character for all chapters, and end of book
      - 'word_count_(subset)': Count of words within (subset)
    """
    def p_params(*args):
        return ("?, " * sum(len(x) for x in args)).rstrip(', ')

    rclass = rclass_id_lookup(cur)

    out = {}
    for k in metadata:
        out[k] = {}

        if k == 'book_titles':
            cur.execute("""
                SELECT b.name
                     , bm.rclass_id
                     , bm.content
                  FROM book b, book_metadata bm
                 WHERE b.book_id = bm.book_id
                   AND b.book_id IN %s
                   AND bm.rclass_id IN %s
            """, (
                tuple(book_ids),
                (rclass['metadata.title'], rclass['metadata.author']),
            ))
            for (book_name, rclass_id, content) in cur:
                if book_name not in out[k]:
                    out[k][book_name] = [None, None]
                out[k][book_name][0 if rclass_id == rclass['metadata.title'] else 1] = content

        elif k == 'chapter_start':
            cur.execute("""
                SELECT b.name
                     , r.rvalue as chapter_num
                     , r.crange crange
                  FROM book b, region r
                 WHERE b.book_id = r.book_id
                   AND r.rclass_id = %s
                   AND b.book_id IN %s
            """, (
                rclass['chapter.text'],
                tuple(book_ids),
            ))
            for (book_name, chapter_num, crange) in cur:
                if book_name not in out[k]:
                    out[k][book_name] = dict()
                out[k][book_name][chapter_num] = crange.lower
                out[k][book_name]['_end'] = max(out[k][book_name].get('_end', 0), crange.upper)

        elif k == 'word_count_chapter':
            cur.execute("""
                SELECT b.name
                     , bwc.rvalue as chapter_num
                     , bwc.word_count
                  FROM book b, book_word_count bwc
                 WHERE b.book_id = bwc.book_id
                   AND bwc.rclass_id = %s
                   AND b.book_id IN %s
              ORDER BY bwc.book_id, bwc.rvalue
            """, (
                rclass['chapter.text'],
                tuple(book_ids),
            ))
            for (book_name, chapter_num, word_total) in cur:
                if book_name not in out[k]:
                    out[k][book_name] = dict(_end=0)
                out[k][book_name][chapter_num] = out[k][book_name]['_end']
                out[k][book_name]['_end'] += int(word_total)

        elif k.startswith('word_count_'):
            api_subset = api_subset_lookup(cur)
            # TODO: word_count_quote not quite matching old CLiC (too high). Why?
            cur.execute("""
                SELECT b.name
                     , SUM(bwc.word_count) AS word_count
                  FROM book b, book_word_count bwc
                 WHERE b.book_id = bwc.book_id
                   AND bwc.rclass_id = %s
                   AND b.book_id IN %s
              GROUP BY b.book_id
            """, (
                api_subset[k.replace('word_count_', '')],
                tuple(book_ids),
            ))
            for (book_name, word_count) in cur:
                out[k][book_name] = int(word_count)

        else:
            raise ValueError("Unknown metadata item %s" % k)

    return out
