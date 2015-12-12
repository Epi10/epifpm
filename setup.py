__author__ = 'aleivag'
import os
from distutils.core import setup


import os
from distutils.core import setup

try:
    f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
    long_description = f.read()
    f.close()
except:
    long_description = ''


reqs = []

try:
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        reqs.extend(map(lambda x: x.strip(), f))
except:
    pass


setup(
    name='epifpm',
    version=__version__,
    packages=['epifpm'],
    author='Alvaro Leiva',
    author_email='aleivag@gmail.com',
    url='https://github.com/Epi10/epifpm',
    #download_url='https://github.com/Epi10/pyngdom/releases/tag/%s' % __version__,
    classifiers=[
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities"
    ],
    keywords=['fingerprint', 'serial'],
    description='library to read from fingerprint scaners in python',
    long_description=long_description,
    install_requires=reqs,
    license='MIT'
)
