from importlib.metadata import entry_points
from setuptools import setup, find_packages


setup(
    name="conicfinance",
    packages=find_packages(),
    install_requires=[
        "web3",
        "tqdm",
        "matplotlib",
    ],
    entry_points={
        "console_scripts": ["conicfinance=conicfinance.cli:main"],
    },
)
