import os
from setuptools import setup, find_packages
from glob import glob


def find_scripts():
    scripts = []
    for file in glob(os.path.join("bin", "*")):
        scripts.append(file)
    print("Adding scripts: {}".format(scripts))
    return scripts


def find_data_files():
    files = glob(os.path.join("config", "*"))
    print("Adding data files: {}".format(files))
    return files


def find_requirements():
    with open('requirements.txt') as f:
        requirements = f.read().splitlines()
    return requirements


args = dict(
    name="World-of-Warships-Stats-Analysis",
    version="0.1",
    author="Moliang",
    description="WOWS data web",
    license="MIT",
    packages=find_packages(),
    install_requires=find_requirements(),
    data_files=[("config", find_data_files())],
    scripts=find_scripts(),
    python_requires=">=3.6"
)

setup(**args)
