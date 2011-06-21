from setuptools import setup, find_packages

version = '1.0'

setup(name='asmmobile',
      version=version,
      description="",
      long_description="""\
""",
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords="",
      author="",
      author_email="",
      url="",
      license="",
      package_dir={'': 'src'},
      packages=find_packages('src'),
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'grok',
                        'grokui.admin',
                        'fanstatic',
                        'zope.fanstatic',
                        'grokcore.startup',
                        # Add extra requirements here
                        'z3c.testsetup',
                        'icalendar',
                        'zif.gzipper',
                        # Dateutil version < 2 works with Python 2.x series.
                        'python-dateutil==1.5',
                        'repoze.profile',
                        ],
      entry_points={
          'fanstatic.libraries': [
              'asmmobile = asmmobile.resource:library',
          ]
      })
