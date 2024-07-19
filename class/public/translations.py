# Language translations
import os
import glob
import json
import public

translations = {}


# Load translations
def load_translations():
    if len(translations.keys()) > 0:
        return translations

    scan_pattern = '{}/BTPanel/static/vite/lang/*/*.json'.format(public.get_panel_path())

    for path in glob.glob(scan_pattern):
        lan = os.path.basename(os.path.dirname(path))
        if lan not in translations:
            translations[lan] = {}
        with open(path, 'r') as fp:
            translations[lan].update(json.loads(fp.read()))

    return translations
