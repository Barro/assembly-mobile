IMPORTERS = {
    'icalendar': {
        'filename': '/tmp/asmtv.ics',
        'locationMap': {'none': 'AssemblyTV'},
        },
    'asmcsv': {
        'filename': '/tmp/schedule.csv',
        'prefix': 'asm',
        'language': 'EN',
        }
    }

MAPPING_LOCATIONS = {
    'Big screen': 'MAIN-ARENA',
    'Stage': 'MAIN-ARENA',
    }


PRIORITIES = {
    'MAIN-ARENA': 10,
    'Seminar hall': 9,
    'Game hall': 7,
    'PMS': 6,
    'AssemblyTV': 4,
    'Infodesk': -1,
    }
