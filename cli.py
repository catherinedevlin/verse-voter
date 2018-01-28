# -*- coding: utf-8 -*-
"""Console script for verse_voter."""

import click

from vv import commands

# models.db.bind(provider='postgres', database='pvv')
# models.db.bind(provider='postgres', database='verse_voter')
# models.db.generate_mapping()


@click.group()
def main(args=None):
    """Console script for verse_voter."""
    click.echo("See click documentation at http://click.pocoo.org/")


@main.command()
def read_from_reddit():
    """Pull current voting results from reddit to database"""

    return commands.read_from_reddit()


@main.command()
def write_to_reddit():
    """Push from database to reddit"""

    return commands.write_to_reddit()


@main.command()
def write_site():
    """Generate Markdown pages with current database contents"""

    return commands.write_site()
