import shlex
from subprocess import check_output, CalledProcessError
from setuptools import setup, find_packages


LONG_DESCRIPTION="""
This package contains a python library and a command line to extract data from [Eco-Adapt Power Elec 3 or 6](https://www.eco-adapt.com/products/)
and export that data to a cloud server using websockets.
"""

def git_to_pep440(git_version):
    """ Transforms the git version to an allowed pep404 version. """
    if '-' not in git_version:
        return git_version

    sep = git_version.index('-')
    version = git_version[:sep] + '+dev' + git_version[sep+1:].replace('-', '.')
    return version


def git_version() -> str:
    """ Use git latest tag to determine the version of the package.

    :return: the short SHA of the git repository.
    """
    cmd = 'git describe --tags --always --dirty --match v[0-9]*'
    try:
        git_version = check_output(shlex.split(cmd)).decode('utf-8').strip()[1:]
    except CalledProcessError as e:
        raise Exception('Could not get git version') from e
    return git_to_pep440(git_version)


def read_requirements(requirements_file: str) -> list:
    """ Read a requirements file and return its content.

    :param requirements_file: the file that holds the requirements.
    :returns: a list with all the requirements stored in the file
    """
    with open(requirements_file) as f:
        install_requires = f.read().splitlines()

    return install_requires


setup(
    name="exporter_ecoadapt",
    version=git_version(),
    description="Tool used to communicate with Eco-Adapt Power Elect.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/marifante/iot-python-assignment",
    author="Julian Rodriguez",
    author_email="junirodriguezz1@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        'Operating System :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "exporter_ecoadapt=exporter_ecoadapt.cli:main",
        ],
    },
    python_requires=">=3.7, <4",
    install_requires=read_requirements("requirements.txt")
)

