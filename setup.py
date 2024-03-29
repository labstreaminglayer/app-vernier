from setuptools import setup
from pathlib import Path

with (Path(__file__).parent / "readme.md").open() as f:
    long_description = f.read()

with (Path(__file__).parent / "requirements.txt").open() as f:
    install_requires = f.readlines()

setup(
    name="vernier-lsl",
    version="0.2.1",
    description="Toolbox to receive godirect data and send as LSL streams.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Robert Guggenberger",
    author_email="robert.guggenberger@uni-tuebingen.de",
    url="https://github.com/translationalneurosurgery/app-vernier.git",
    download_url="https://github.com/translationalneurosurgery/app-vernier.git",
    license="MIT",
    packages=["verniersl"],
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "verniersl=verniersl.__main__:main",
            "vernier-lsl=verniersl.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries",
    ],
)
