import os
from setuptools import setup, find_packages
from setuptools.command.install import install


# class CustomInstallCommand(install):
#     # This is only run for "python setup.py install" (not for "pip install -e .")
#     def run(self):
#         print("--------------------------------")
#         print("Writing environment variables to .env ...")
#         os.system('echo "export DELORA_ROOT=' + os.getcwd() + '" >> .env')
#         print("...done.")
#         print("--------------------------------")
#         install.run(self)


setup(name='LunarPathPlanner',
      version='1.0',
      author='Julia Richter (jurichter@ethz.ch)',
      package_dir={"": "src"},
    #   install_requires=[
    #       'numpy',
    #       'torch',
    #       'opencv-python',
    #       'pyyaml',
    #       'rospkg'
    #   ],
      scripts=['examples/main_globalplanner.py'],
      license='LICENSE',
      description='Global path planner for lunar applications',
    #   cmdclass={'install': CustomInstallCommand, },
      )