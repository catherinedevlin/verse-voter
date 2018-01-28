from datetime import datetime
from os.path import join
from random import random
from time import sleep

from pony import orm

from .helpers import get_config
from .models import Project, Verse
from .reddit import get_subreddit


@orm.db_session
def read_from_reddit():
    config = get_config()
    project_name = config['WEBSITE']['project']
    subreddit = get_subreddit()

    for submission in subreddit.submissions():
        if submission.comments:
            comment = submission.comments[0]  # automatically sorts top comment
            verse = Verse.get(topic_url=submission.id)
            if verse:
                verse.result_text = comment.body
                verse.last_modified = datetime.fromtimestamp(comment.created_utc)

@orm.db_session
def write_to_reddit():
    config = get_config()
    project_name = config['WEBSITE']['project']
    subreddit = get_subreddit()

    # update existing verses
    for submission in subreddit.submissions():
        verse = Verse.get(topic_url=submission.id)
        if verse:
            newbody = verse.reddit_markdown()
            if submission.selftext != newbody:
                print(f'Pushing edit to {verse.name}')
                submission.edit(newbody)
                sleep(random())

    # initial push of new verses
    for verse in Verse.select(lambda v: v.topic_url is None):
        verse.push_to_reddit(subreddit)
        print(f'pushed {verse.name}')
        sleep(random())
        break

@orm.db_session
def write_site():
    config = get_config()
    project_name = config['WEBSITE']['project']
    project = Project.get(name=project_name)
    project.write_site(config['WEBSITE']['path'])
