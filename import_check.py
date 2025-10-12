import sys
sys.path.insert(0, r'C:\Users\carlo\U\EntrenaProChile')

try:
    import backend
    print('Imported backend')
    from database import database as models
    model_names = [name for name in dir(models) if not name.startswith('_')]
    print('Imported database.models ->', model_names)
except Exception as e:
    print('ERROR during import:', repr(e))
    raise
