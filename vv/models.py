from datetime import datetime
from os import makedirs
from os.path import join
from textwrap import dedent

from pony import orm
from slugify import slugify

from .helpers import get_config

db = orm.Database()
config = get_config()
db.bind(provider=config['DATABASE']['provider'], database=config['DATABASE']['database'])


WEBSITE_VERSE_TEMPLATE = '''
[{n}](topic_url) {result_text}
'''


JEKYLL_FRONT_MATTER = '''---
layout: page
title: {title}
---

# {title}

'''

class SlugifiedMixin:

    @property
    def slug(self):
        return slugify(self.name)


class Project(db.Entity, SlugifiedMixin):
    name = orm.Required(str)
    books = orm.Set('Book')
    last_modified = orm.Optional(datetime)
    notes = orm.Optional(str)

    @property
    def path(self):
        return f'/{self.slug}'

    def markdown(self):
        yield JEKYLL_FRONT_MATTER.format(title=self.name)
        for book in self.books.order_by(Book.n):
            yield f'- [{book.name}]({book.path}.html)\n'
        yield f"\n\n[Project source code]({config['WEBSITE']['github']})"

    def write_site(self, path):
        path = join(path, self.slug)
        with open(path + '.md', 'w') as outfile:
            outfile.writelines(self.markdown())
        makedirs(path, exist_ok=True)
        for book in self.books:
            book.write_site(path)


class Book(db.Entity, SlugifiedMixin):
    name = orm.Required(str)
    n = orm.Required(int)
    project_id = orm.Required(Project)
    edition = orm.Optional(str)
    chapters = orm.Set('Chapter')
    last_modified = orm.Optional(datetime)
    notes = orm.Optional(str)

    @property
    def path(self):
        return f'{self.project_id.path}/{self.slug}'


    INDEX_TEMPLATE = '[{self.name}]({self.path})'

    def index_of(self):
        return self.INDEX_TEMPLATE.format(**locals)

    CHAPTER_LINK_TEMPLATE = '- [{c.n}](c.slug)'

    def markdown(self):
        yield JEKYLL_FRONT_MATTER.format(title=self.name)
        yield from self.links()
        for c in self.chapters.order_by(Chapter.n):
            yield f'- [{c.n}]({c.path}.html)\n'

    def write_site(self, path):
        path = join(path, self.slug)
        with open(path + '.md', 'w') as outfile:
            outfile.writelines(self.markdown())
        makedirs(path, exist_ok=True)
        for chapter in self.chapters:
            chapter.write_site(path)

    def neighbor(self, stepsize):
        "Gets book with n offset `stepsize` from `self`"
        return self.project_id.books.select(lambda b: b.n == self.n + stepsize).first()

    def links(self):
        yield f'\n[{self.project_id.name}]({self.project_id.path}.html)\n\n'
        prev = self.neighbor(-1)
        if prev:
            yield f'\n[prev: {prev.name}]({prev.path}.html)\n\n'
        next = self.neighbor(+1)
        if next:
            yield f'\n[next: {next.name}]({next.path}.html)\n\n'



class Chapter(db.Entity, SlugifiedMixin):
    n = orm.Required(int)
    book_id = orm.Required(Book)
    verses = orm.Set('Verse')
    last_modified = orm.Optional(datetime)
    notes = orm.Optional(str)

    @property
    def name(self):
        return f'{self.book_id.name} {self.n}'

    @property
    def path(self):
        return f'{self.book_id.path}/{self.slug}'


    def markdown(self):
        title = f'[{self.book_id.name}]({self.book_id.path}.html) {self.n}'
        yield JEKYLL_FRONT_MATTER.format(title=title)
        yield from self.links()
        for v in self.verses.order_by(Verse.n):
            yield from v.markdown()

    def write_site(self, path):
        path = join(path, self.slug)
        with open(path + '.md', 'w') as outfile:
            outfile.writelines(self.markdown())

    def neighbor(self, stepsize):
        "Gets chapter with n offset `stepsize` from `self`"
        return self.book_id.chapters.select(lambda c: c.n == self.n + stepsize).first()

    def links(self):
        yield f'[{self.book_id.project_id.name}]({self.book_id.project_id.path}.html)\n\n'
        prev = self.neighbor(-1)
        if prev:
            yield f'\n[prev]({prev.path}.html)\n\n'
        next = self.neighbor(+1)
        if next:
            yield f'\n[next]({next.path}.html)\n\n'




class Verse(db.Entity):
    n = orm.Required(int)
    chapter_id = orm.Required(Chapter)
    topic_url = orm.Optional(str)
    reference_text = orm.Required(str)
    result_text = orm.Optional(str)
    last_modified = orm.Optional(datetime)

    @property
    def name(self):
        return f'{self.chapter_id.name}:{self.n}'

    def markdown(self):
        if self.result_text:
            text = self.result_text
        else:
            text = f'_{self.reference_text}_'

        if self.topic_url:
            verseno = f'[{self.n}](https://reddit.com/{self.topic_url})'
        else:
            verseno = self.n

        yield f'{verseno} {text}\n\n'


    def reddit_markdown(self):
        return dedent(f'''
            {self.reference_text}

            [BibleGateway](https://www.biblegateway.com/passage/?search={self.chapter_id.book_id.name}+{self.chapter_id.n}:{self.n})

            [{self.chapter_id.book_id.name}]({config['WEBSITE']['ghpage']}{self.chapter_id.book_id.path}.html)
            [{self.chapter_id.n}]({config['WEBSITE']['ghpage']}{self.chapter_id.path}.html)
            ''')

    def push_to_reddit(self, subreddit):
        if self.topic_url:
            raise NotImplemented('Re-pushing not implemented')
        else:
            thread = subreddit.submit(title=self.name, selftext=self.reddit_markdown())
            self.topic_url = thread.shortlink

    def submission(self, reddit_conn):
        return reddit_conn.submission(self.topic_url)

    def get_result_text(self, reddit_conn):
        try:
            # sorts by best comments by default
            self.result_text = self.submission(reddit_conn).comments[0]
        except IndexError:
            # no top comment, do nothing
            pass

    def website_markdown(self):
        return WEBSITE_VERSE_TEMPLATE.format(**self.__dict__)


db.generate_mapping()
