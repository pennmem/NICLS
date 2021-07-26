import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='NICLServer',
    version='0.2.1',
    maintainer=['James Bruska', 'Joey Rudoler'],
    maintainer_email=['jbruska@sas.upenn.edu', 'jrudoler@sas.upenn.edu', 'kahana-sysadmin@sas.upenn.edu'],
    url='https://github.com/pennmem/NICLS',
    description = ("The backend system used to control the NICLS experiment"),
    long_description=read('README.md'),

    install_requires=[
        "numpy",
        "scikit-learn",
        "django",
        "aiofiles",
        "zmq",
    ],
)


