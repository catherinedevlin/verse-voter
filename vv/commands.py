from datetime import datetime
from os.path import join

from pony import orm

from .models import Project, Verse
from .helpers import get_config
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
def write_site():
    config = get_config()
    project_name = config['WEBSITE']['project']
    project = Project.get(name=project_name)
    project.write_site(config['WEBSITE']['path'])


