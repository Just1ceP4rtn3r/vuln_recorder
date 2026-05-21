from setuptools import setup, find_packages

setup(
    name='vuln-recorder',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['PyYAML'],
    entry_points={
        'console_scripts': ['vuln-recorder=vuln_recorder.cli:main'],
    },
)
