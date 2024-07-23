import os
import re
import time
import logging
from typing import List, Dict, Optional
import requests
from github import Github, GithubException, Repository
from packaging import version, specifiers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DependencyChecker:
    def __init__(self, github_token: Optional[str], repositories: list):
        self.github = Github(github_token) if github_token else Github()
        self.repositories = repositories
        self.file_paths = [
            "requirements.txt",
            "requirements.lock",
            "setup.py",
            "Pipfile",
        ]

    def check(self) -> None:
        for repo in self.repositories:
            self.check_and_update_repo(repo)
            print("")  # Add a blank line for readability

    def get_latest_version(self, package_name: str) -> Optional[str]:
        """Fetch the latest stable version of a package from PyPI."""
        if not package_name:
            return None

        # Skip built-in or standard library modules
        standard_libs = {
            "sys",
            "os",
            "re",
            "time",
            "logging",
            "json",
            "requests",
            "from",
            "import",
            "def",
        }

        if package_name in standard_libs:
            logger.info(f"Skipping standard library module: {package_name}")
            return None

        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            response = requests.get(url)
            logger.info(
                f"Response from PyPI for {package_name}: {url} {response.status_code}"
            )
            response.raise_for_status()
            data = response.json()

            latest_version = data["info"]["version"]
            logger.info(f"Latest version for {package_name}: {latest_version}")
            return latest_version
        except requests.RequestException as e:
            logger.error(f"Error fetching version for {package_name}: {str(e)}")
            return None

    def parse_requirement(self, req: str) -> Dict[str, str]:
        """Parse a requirement string into package name and version specifier."""
        # Remove quotes if present
        req = req.strip("'\"")

        # Skip invalid lines
        if req.startswith(("--", "-e", "from", "import", "def", "os", "sys")):
            return {"name": "", "spec": "", "operator": ""}

        match = re.match(r"([^<>=!~\s]+)([<>=!~].+)?", req)
        if match:
            name = match.group(1).strip()
            spec = (match.group(2) or "").strip()
            return {
                "name": name,
                "spec": spec,
                "operator": re.match(r"([<>=!~]+)", spec).group(1) if spec else "",
            }
        return {"name": req.strip(), "spec": "", "operator": ""}

    def check_update_needed(self, current_spec: str, latest_version: str) -> bool:
        """Check if an update is needed based on the current specifier and latest version."""
        if not current_spec:
            return True

        try:
            spec = specifiers.SpecifierSet(current_spec)
            latest = version.parse(latest_version)

            if current_spec.startswith("~="):
                current = version.parse(current_spec[2:])
                return latest > current and latest.release[:2] == current.release[:2]

            return not spec.contains(latest_version)
        except (version.InvalidVersion, specifiers.InvalidSpecifier):
            # If parsing fails, assume an update is needed
            return True

    def update_requirement(self, req: str, latest_version: str) -> str:
        """Update a requirement string with the latest version."""
        parsed = self.parse_requirement(req)
        if parsed["spec"]:
            if parsed["operator"] == "~=":
                return f"{parsed['name']}~={latest_version}"
            else:
                return f"{parsed['name']}{parsed['operator']}{latest_version}"
        return f"{parsed['name']}=={latest_version}"

    def run_tests(self, repo_name: str, branch_name: str) -> bool:
        """Run tests on the specified branch."""
        # Test scenario, you would trigger your CI/CD pipeline here.
        try:
            repo = self.github.get_repo(repo_name)
            logger.info(f"Successfully accessed repository: {repo_name}")

            # Assuming the tests are defined in a script called 'run_tests.sh' in the repo
            command = f"cd {repo_name} && git checkout {branch_name} && ./run_tests.sh"
            result = os.system(command)

            if result == 0:
                logger.info(f"Tests passed on branch {branch_name}")
                return True
            else:
                logger.error(f"Tests failed on branch {branch_name}")
                return False
        except Exception as e:
            logger.error(
                f"Error running tests on {repo_name} branch {branch_name}: {str(e)}"
            )
            return False

    def get_dependency_updates(self) -> Dict[str, List[Dict[str, str]]]:
        """Get the dependency updates for the specified files."""
        updates = {}
        for file_path in self.file_paths:
            try:
                with open(file_path, "r") as file:
                    lines = file.readlines()

                file_updates = []
                for line in lines:
                    req = self.parse_requirement(line)
                    latest_version = self.get_latest_version(req["name"])
                    if latest_version and self.check_update_needed(
                        req["spec"], latest_version
                    ):
                        file_updates.append(
                            {
                                "old": line.strip(),
                                "new": f"{req['name']}=={latest_version}",
                            }
                        )

                if file_updates:
                    updates[file_path] = file_updates

            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

        return updates

    def generate_requirements(self, repo, branch):
        try:
            contents = repo.get_contents("", ref=branch)
            python_files = [
                content.path for content in contents if content.path.endswith(".py")
            ]

            requirements = set()
            for file_path in python_files:
                file_content = repo.get_contents(file_path, ref=branch)
                content = file_content.decoded_content.decode()
                imports = re.findall(
                    r"^import\s+(\w+)|^from\s+(\w+)", content, re.MULTILINE
                )
                requirements.update([imp[0] or imp[1] for imp in imports])

            return "\n".join(sorted(requirements))
        except Exception as e:
            logger.error(f"Error generating requirements: {str(e)}")
            return None

    def process_file_content(self, content, file_path):
        if file_path == "requirements.txt":
            requirements = content.split("\n")
            file_updates = []
            for req in requirements:
                req = req.strip()
                if req and not req.startswith("#"):
                    parsed_req = self.parse_requirement(req)
                    latest_version = self.get_latest_version(parsed_req["name"])
                    if latest_version:
                        updated_req = f"{parsed_req['name']}=={latest_version}"
                        if updated_req != req:
                            file_updates.append({"old": req, "new": updated_req})
            return file_updates
        else:
            # Processing for other file types...
            if file_path.endswith(".py"):
                imports = re.findall(
                    r"^import\s+(\w+)|^from\s+(\w+)", content, re.MULTILINE
                )
                return [{"import": imp[0] or imp[1]} for imp in imports]
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return []

    def check_dependencies(
        self, repo: Repository.Repository
    ) -> Dict[str, List[Dict[str, str]]]:
        updates = {}

        for file_path in self.file_paths:
            try:
                # Check if the file exists in the repository
                contents = repo.get_contents("")
                file_names = [content.path for content in contents]
                if file_path not in file_names:
                    logger.warning(
                        f"File {file_path} does not exist in the repository."
                    )
                    continue

                file_content = repo.get_contents(file_path)
                content = file_content.decoded_content.decode()

                if file_path == "setup.py":
                    # Extract only the install_requires list from setup.py
                    install_requires_match = re.search(
                        r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
                    )
                    if install_requires_match:
                        requirements = re.findall(
                            r"'([^']+)'", install_requires_match.group(1)
                        )
                    else:
                        requirements = []
                else:
                    requirements = re.findall(r"^[^#\n]+", content, re.MULTILINE)

                file_updates = []
                for req in requirements:
                    parsed_req = self.parse_requirement(req)
                    latest_version = self.get_latest_version(parsed_req["name"])
                    if latest_version:
                        current_version = parsed_req["spec"].lstrip("=~<>!")
                        if self.check_update_needed(current_version, latest_version):
                            updated_req = self.update_requirement(req, latest_version)
                            if req != updated_req:  # Check if old and new are different
                                file_updates.append({"old": req, "new": updated_req})
                                logger.info(
                                    f"Update available in {file_path}: {req} -> {updated_req}"
                                )

                if file_updates:
                    updates[file_path] = file_updates
            except GithubException as e:
                logger.error(f"Error accessing file {file_path}: {e}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

        return updates

    def create_fork_and_branch(
        self, repo: Repository.Repository, branch_name: str
    ) -> Optional[Repository.Repository]:
        try:
            fork = self.github.get_user().create_fork(repo)
            time.sleep(5)  # Wait for the fork to be created
            fork.create_git_ref(
                f"refs/heads/{branch_name}",
                fork.get_branch(repo.default_branch).commit.sha,
            )
            return fork
        except GithubException as e:
            logger.error(f"Error creating fork or branch: {e}")
            return None

    def create_branch(self, repo: Repository.Repository, branch_name: str):
        try:
            source = repo.get_branch(repo.default_branch)
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
            logger.info(f"Created branch {branch_name} in repository {repo.full_name}")
        except GithubException as e:
            logger.error(f"Error creating branch: {e}")
            raise

    def create_pull_request(
        self,
        original_repo: Repository.Repository,
        source_repo: Repository.Repository,
        branch_name: str,
        updates: Dict[str, List[Dict[str, str]]],
    ) -> Optional[str]:
        if not updates:
            logger.info("No updates needed.")
            return None

        try:
            for file_path, file_updates in updates.items():
                try:
                    file_content = source_repo.get_contents(file_path, ref=branch_name)
                    content = file_content.decoded_content.decode()

                    for update in file_updates:
                        content = content.replace(update["old"], update["new"])

                    source_repo.update_file(
                        file_path,
                        f"Update dependencies in {file_path}",
                        content,
                        file_content.sha,
                        branch=branch_name,
                    )
                except Exception as e:
                    logger.error(f"Error updating {file_path}: {str(e)}")

            # Create pull request
            pr = original_repo.create_pull(
                title="Update Dependencies",
                body="This PR updates project dependencies to their latest versions.",
                head=(
                    f"{source_repo.owner.login}:{branch_name}"
                    if source_repo != original_repo
                    else branch_name
                ),
                base=original_repo.default_branch,
            )

            logger.info(f"Created Pull Request: {pr.html_url}")
            return pr.html_url
        except GithubException as e:
            logger.error(f"GitHub API error: {e.status} - {e.data.get('message')}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def review_changes(
        self, updates: Dict[str, List[Dict[str, str]]]
    ) -> Dict[str, List[Dict[str, str]]]:
        approved_updates = {}
        for file_path, file_updates in updates.items():
            approved_file_updates = []
            print(f"Reviewing changes for {file_path}:")
            for update in file_updates:
                print(f"  Old: {update['old']}")
                print(f"  New: {update['new']}")
                approval = input("Approve this change? (y/n): ").lower().strip()
                if approval == "y":
                    approved_file_updates.append(update)
                print()  # Add a blank line for readability
            if approved_file_updates:
                approved_updates[file_path] = approved_file_updates
        return approved_updates

    def check_and_update_repo(self, repo_name: str) -> Optional[str]:
        try:
            original_repo = self.github.get_repo(repo_name)
            logger.info(f"Successfully accessed repository: {repo_name}")

            updates = self.check_dependencies(original_repo)

            if not updates:
                logger.info("No dependency updates found.")
                return None

            approved_updates = self.review_changes(updates)

            if not approved_updates:
                logger.info(
                    "No changes were approved. Exiting without creating a pull request."
                )
                return None

            branch_name = f"update-dependencies-{int(time.time())}"

            # Read and confirm the whole file before publishing
            for file_path, file_updates in approved_updates.items():
                try:
                    file_content = original_repo.get_contents(file_path)
                    content = file_content.decoded_content.decode()
                    print(f"Reviewing final content for {file_path}:")
                    print(content)
                    approval = (
                        input("Approve this file for publishing? (y/n): ")
                        .lower()
                        .strip()
                    )
                    if approval != "y":
                        logger.info(f"Publishing of {file_path} was not approved.")
                        return None
                except Exception as e:
                    logger.error(
                        f"Error reading final content of {file_path}: {str(e)}"
                    )
                    return None

            if original_repo.permissions.push:
                # We have write access, create branch directly
                self.create_branch(original_repo, branch_name)
                source_repo = original_repo
            else:
                # We don't have write access, try to fork
                source_repo = self.create_fork_and_branch(original_repo, branch_name)
                if not source_repo:
                    logger.error("Failed to create fork or branch.")
                    return None

            pr_url = self.create_pull_request(
                original_repo, source_repo, branch_name, approved_updates
            )

            return pr_url
        except GithubException as e:
            logger.error(f"GitHub API error: {e.status} - {e.data.get('message')}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
