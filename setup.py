from pathlib import Path

from setuptools import setup

from pbatch import version

ROOT_DIRECTORY = Path(__file__).resolve().parent

description = "Parallel batch processing on top of regular python functions"
readme = (ROOT_DIRECTORY / "README.md").read_text()
changelog = (ROOT_DIRECTORY / "CHANGELOG.md").read_text()
long_description = readme + "\n\n" + changelog


DEV_REQUIRES = [
    "black==20.8b1",
    "coverage==5.2.1",
    "flake8==3.8.3",
    "flake8-bugbear==20.1.4",
    "isort==5.5.1",
    "mypy==0.782",
    "pre-commit==2.7.1",
    "pytest==6.0.1",
    "pytest-cov==2.10.1",
    "pytest-mock==3.3.1",
    "tox==3.20.0",
]

setup(
    name="pbatch",
    version=version.VERSION,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    author="Naya Verdier",
    url="https://github.com/nayaverdier/pbatch",
    license="MIT",
    packages=["pbatch"],
    python_requires=">=3.7",
    extras_require={
        "dev": DEV_REQUIRES,
        # "docs": DOCS_REQUIRES,
    },
)
