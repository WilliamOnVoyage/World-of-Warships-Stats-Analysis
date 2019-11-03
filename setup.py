import re

from setuptools import setup, find_packages
from glob import glob


def find_scripts():
    scripts = []
    for file in glob("bin/*"):
        with open(file, "r") as f:
            if re.search(r'^#!.*', f.readline()):
                scripts.append(file)
    return scripts


def find_data_files():
    files = glob("config/*.json")
    return files


def find_requirements():
    with open('requirements.txt') as f:
        requirements = f.read().splitlines()
    return requirements


args = dict(
    name="World-of-Warships-Stats-Analysis",
    version="0.1",
    author="Moliang",
    description="Python core for WOWS data collection and analysis",
    license="MIT",
    packages=find_packages(),
    install_requires=find_requirements(),
    data_files=[("config", find_data_files())],
    scripts=find_scripts(),
    python_requires=">=3.6"
)

setup(**args)
