from setuptools import setup, find_packages

setup(name='Algorithm simulator',
      version='2.0',
      description='Distributed algorithm simulator for exploring state space',
      author='Jan Homola',
      author_email='janhomola92@gmail.com',
      url='https://github.com/hon92/Algorithm-simulator',
      packages=find_packages(),
      package_data = {
            "src" : ["resources/icons/*.png", "resources/glade_dialogs/*.glade"]
      },
      data_files = [("", ["__main__.py"])]
     )