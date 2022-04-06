from importlib.metadata import entry_points
from setuptools import setup


setup(
    name="conicfinance",
    install_requires=[
        "web3",
        "tqdm",
    ],
    entry_points={
        "console_scripts": ["conicfinance=conicfinance.cli:main"],
    },
)
