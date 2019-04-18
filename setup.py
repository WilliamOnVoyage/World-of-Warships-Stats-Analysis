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


args = dict(
    name="World-of-Warships-Stats-Analysis",
    version="0.1",
    author="William on Voyage",
    description="Python core for WOWS data collection and analysis",
    license="MIT",
    packages=["wows_stats"],
    data_files=[("config", find_data_files())],
    scripts=find_scripts(),
)

setup(**args)
