# PackagePatrol

## Overview

The PackagePatrol is a Python tool designed to automate the process of checking, updating, and managing dependencies in GitHub repositories. It streamlines the process of ensuring that all dependencies are up-to-date, which helps maintain the security and stability of your projects.

## Features

- **Automatic Dependency Checking**: Scans specified files (e.g., requirements.txt, setup.py) for dependencies and checks if they are up-to-date.
- **Dependency Updates**: Fetches the latest stable versions of packages from PyPI and updates the specified files.
- **Branch Creation**: Creates a new branch for the dependency updates.
- **Pull Request Creation**: Automatically creates a pull request with the updated dependencies.
- **Interactive Review**: Allows manual review and approval of each change before creating a pull request.

## Prerequisites

- Python 3.7 or later
- GitHub account and a classic [personal access token](https://github.com/settings/tokens/) with appropriate permissions and the following scopes:
  - repo (all)
  - read:org

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/jan890/PackagePatrol.git
   cd PackagePatrol
   ```

2. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

## Configuration

- **GitHub Token**: Create a GitHub personal access token with repo and workflow permissions. Store this token securely as it grants access to your repositories.
- **Repositories List**: Define the list of repositories you want to check and update. This should be a list of repository names in the format username/repo_name.

## Usage

1. Initialize the PackagePatrol:

   ```python
   from PackagePatrol import DependencyChecker

   github_token = "your_github_token"
   repositories = [
       "username/repo1",
       "username/repo2"
   ]

   checker = DependencyChecker(github_token, repositories)
   ```

2. Run the Checker:

   ```python
   checker.check()
   ```

## Workflow

1. **Check Dependencies**: The tool will check the specified files in each repository for outdated dependencies.
2. **Generate Updates**: If updates are found, it will create a new branch and update the dependencies.
3. **Run Tests**: The tool will attempt to run tests on the new branch to ensure compatibility.
4. **Create Pull Request**: If the tests pass, it will create a pull request for the updates.
5. **Manual Review**: You can manually review and approve each change before the pull request is created.

## Error Handling

The tool has robust error handling to log and manage exceptions gracefully.
It includes detailed logging to help trace the flow and catch errors.

## Contributions

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
