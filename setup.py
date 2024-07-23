from setuptools import setup, find_packages

setup(
    name="PackagePatrol",
    version="0.2.5",
    packages=find_packages(),
    install_requires=["requests", "PyGithub", "packaging"],
    author="jan890",
    author_email="17707208+jan890@users.noreply.github.com",
    description="A package to check and update project dependencies on GitHub",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jan890/PackagePatrol",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
