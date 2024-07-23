from PackagePatrol import DependencyChecker

if __name__ == "__main__":
    github_token = "your_github_token"
    repositories = [
        "username/repo1",
        "username/repo2",
    ]  # TODO: Replace with your repositories

    checker = DependencyChecker(github_token, repositories)
    checker.check()
