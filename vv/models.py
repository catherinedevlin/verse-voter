from os.path import join
from os import makedirs

from pony import orm
from datetime import datetime
from slugify import slugify

from .helpers import get_config

db = orm.Database()
db_config = get_config()['DATABASE']
db.bind(provider=db_config['provider'], database=db_config['database'])
# try:
#     db.generate_mapping()
# except orm.core.ERDiagramError:
#     pass


REDDIT_VERSE_TEMPLATE = '''
{reference_text}

[BibleGateway](https://www.biblegateway.com/passage/?search={citation})
- [Interlinear Bible]()

[{chapter.book.name}]({chapter.book.path}) [{chapter.n}]({chapter.path})
'''

WEBSITE_VERSE_TEMPLATE = '''
[{n}](topic_url) {result_text}
'''


class Project(db.Entity):
    name = orm.Required(str)
    books = orm.Set('Book')
    last_modified = orm.Optional(datetime)
    # last_modified = Column(DateTime(timezone=True), onupdate=func.now())
    notes = orm.Optional(str)

    def markdown(self):
        for book in self.books.order_by(Book.n):
            yield f'- [{book.name}]({slugify(book.name)}.md)\n'

    def write_site(self, path):
        path = join(path, slugify(self.name))
        with open(path + '.md', 'w') as outfile:
            outfile.writelines(self.markdown())
        makedirs(path, exist_ok=True)
        for book in self.books:
            book.write_site(path)


class Book(db.Entity):
    name = orm.Required(str)
    n = orm.Required(int)
    project_id = orm.Required(Project)
    edition = orm.Optional(str)
    chapters = orm.Set('Chapter')
    last_modified = orm.Optional(datetime)
    notes = orm.Optional(str)

    INDEX_TEMPLATE = '[{self.name}]({self.path})'

    def index_of(self):
        return self.INDEX_TEMPLATE.format(**locals)

    CHAPTER_LINK_TEMPLATE = '- [{c.n}](slugify(c.name))'

    def markdown(self):
        for c in self.chapters.order_by(Chapter.n):
            yield f'- [{c.n}]({slugify(c.name)}.md)\n'

    def write_site(self, path):
        path = join(path, slugify(self.name))
        with open(path + '.md', 'w') as outfile:
            outfile.writelines(self.markdown())
        makedirs(path, exist_ok=True)
        for chapter in self.chapters:
            chapter.write_site(path)



class Chapter(db.Entity):
    n = orm.Required(int)
    book_id = orm.Required(Book)
    verses = orm.Set('Verse')
    last_modified = orm.Optional(datetime)
    notes = orm.Optional(str)

    @property
    def name(self):
        return f'{self.book_id.name} {self.n}'

    def markdown(self):
        for v in self.verses.order_by(Verse.n):
            yield from v.markdown()

    def write_site(self, path):
        path = join(path, slugify(self.name))
        with open(path + '.md', 'w') as outfile:
            outfile.writelines(self.markdown())


class Verse(db.Entity):
    n = orm.Required(int)
    chapter_id = orm.Required(Chapter)
    topic_url = orm.Optional(str)
    reference_text = orm.Required(str)
    result_text = orm.Optional(str)
    last_modified = orm.Optional(datetime)

    def markdown(self):
        if self.result_text:
            yield f'[{self.n}](https://reddit.com/{self.topic_url})  {self.result_text}\n\n'
        else:
            yield f'[{self.n}](https://reddit.com/{self.topic_url})  _{self.reference_text}_\n\n'

    REDDIT_TEMPLATE = '''
    {reference_text}

    [BibleGateway](https://www.biblegateway.com/passage/?search={citation})
    - [Interlinear Bible]()

    [{chapter.book.name}]({chapter.book.path}) [{chapter.n}]({chapter.path})
    '''

    def reddit_markdown(self):
        return self.REDDIT_TEMPLATE.format(**self.__dict__)

    def push_to_reddit(self, subreddit):
        if self.topic_url:
            raise NotImplemented('Re-pushing not implemented')
        else:
            thread = subreddit.submit(title=self.citation, selftext=self.reddit_markdown())
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