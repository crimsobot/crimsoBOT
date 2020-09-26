import random
import re

import yaml

from crimsobot.utils.tools import clib_path_join


class MadlibsStory:
    def __init__(self, document: dict):
        self.keys = document['keys']
        self.text = document['story_text']
        keys_in_text = set(re.findall(r'\{(.*?)\}', self.text))
        declared_keys = set(document['keys'].keys())

        # We run some validation here quickly to make sure that we don't crash later when we try and format the string
        # during a madlibs game. Essentially we're just making sure that the terms in the story and the terms that
        # madlibs is told to use are the same - because otherwise it will error when we try to use str.format()
        if keys_in_text != declared_keys:
            missing_in_text = ', '.join(key for key in declared_keys if key not in keys_in_text)
            missing_in_declarations = ', '.join(key for key in keys_in_text if key not in declared_keys)
            message = ''.join([
                f'Declared keys and keys present in story "{document["name"]}" do not match! Declarations are missing ',
                f'{missing_in_declarations} and story is missing {missing_in_text}'
            ])

            raise ValueError(message)

        # Terms that should display "as they are" (i.e a key name of "noun" will display as "noun") are marked by
        # setting their key value to ~, or Null/None in the YAML schema - it's an ease of use thing. We compensate
        # for that here by setting the value of each key with an empty value to its name (that's a mouthful I know)
        for term, display_as in self.keys.items():
            if not display_as:
                self.keys[term] = term

    def get_keys(self) -> dict:
        keys = list(self.keys.items())
        random.shuffle(keys)
        return {key: value for key, value in keys}


_ruleset_path = clib_path_join('games', 'rules.yaml')
with open(_ruleset_path, encoding='utf-8', errors='ignore') as rules_file:
    _ruleset = next(yaml.safe_load_all(rules_file.read()))

_madlibs_stories_path = clib_path_join('games', 'madlibs.yaml')
with open(_madlibs_stories_path, encoding='utf-8', errors='ignore') as madlibs_stories_file:
    _madlibs_stories = yaml.safe_load_all(madlibs_stories_file.read())

# these are what should be imported by other scripts
STORIES = [MadlibsStory(story) for story in _madlibs_stories]
CRINGO_RULES = _ruleset['cringo']
EMOJISTORY_RULES = _ruleset['emojistory']
MADLIBS_RULES = _ruleset['madlibs']
