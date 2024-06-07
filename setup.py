# import os
from setuptools import setup
# from setuptools.command.install import install


setup(name='LunarPathPlanner',
      version='1.0',
      author='Julia Richter (jurichter@ethz.ch)',
      package_dir={"": "src"},
      scripts=['examples/main_globalplanner.py'],
      license='LICENSE',
      description='Global path planner for lunar applications',
      )