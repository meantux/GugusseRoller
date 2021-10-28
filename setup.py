from setuptools import setup, Extension
import setuptools
import os
import shutil
import platform

# Note: I do not really support this setup.py file
#       I am creating it just to be sure to be listed
#       in pidng's list of dependents. All instructions
#       for building and using the GugusseRoller are available
#       for free (no string attached) at www.deniscarl.com


setup(
    name="GugusseRoller",
    version="1.1.1",
    author="Denis-Carl Robidoux",
    description="Software to run the DIY Gugusse Roller (to transfer 8mm/super8/Pathex/16mm/35mm fmovies to digital)",
    url="https://github.com/meantux/GugusseRoller",
    packages=['GugusseRoller'],
    install_requires=[
        'pidng'
    ],
    python_requires='>=3.5',
)
