"""Error/resource-leak gate shared by native artifact smoke checks."""
import re


def failed(text):
    return re.search(
        r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance'
        r'|^Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\r?$'
        r'|^StringName: [1-9][0-9]* unclaimed string names at exit\.\r?$',
        text, re.M) is not None
