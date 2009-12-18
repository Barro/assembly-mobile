from setuptools import setup, find_packages

version = '0.0'

setup(name='AsmMobile',
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
                        'z3c.testsetup',
                        'grokcore.startup',
                        # Add extra requirements here
                        'icalendar',
                        'zif.gzipper',
                        'python-dateutil',
                        'repoze.profile',
                        ],
      entry_points = """
      [console_scripts]
      asmmobile-debug = grokcore.startup:interactive_debug_prompt
      asmmobile-ctl = grokcore.startup:zdaemon_controller
      [paste.app_factory]
      main = grokcore.startup:application_factory
      debug = grokcore.startup:debug_application_factory
      """,
      )
