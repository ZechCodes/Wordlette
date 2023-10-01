from contextlib import contextmanager

from bevy import get_repository


@contextmanager
def fork_context():
    repo = get_repository()
    branch = repo.fork_context()
    yield branch
    repo.set_repository(repo)
