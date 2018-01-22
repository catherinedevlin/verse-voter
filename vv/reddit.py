from .helpers import get_config
import praw

def get_reddit():
    config = get_config()
    user_agent = '{platform}:{qualified_name}:v{version} (by /u/{author})'.format(**config['REDDIT'])
    credentials = dict(client_id=config['REDDIT']['client_id'],
                        client_secret=config['REDDIT']['secret'],
                        user_agent=user_agent,
                        username=config['REDDIT']['author'],
                        password=config['REDDIT']['password'])
    reddit = praw.Reddit(**credentials)
    return reddit

def get_subreddit():
    config = get_config()
    reddit_instance = get_reddit()
    subreddit = reddit_instance.subreddit(config['REDDIT']['subreddit'])
    subreddit.reddit = reddit_instance
    return subreddit

