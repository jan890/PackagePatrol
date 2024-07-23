import os
from PackagePatrol import DependencyChecker
from dotenv import load_dotenv

load_dotenv()  # Load the .env file

if __name__ == "__main__":
    github_token = os.environ.get(
        "GITHUB_TOKEN"  # setup your .env file with your github token
    )
    repositories = [
        "username/repo1",
        "username/repo2",
    ]  # TODO: Replace with your repositories

    checker = DependencyChecker(github_token, repositories)
    checker.check()
