"""Error/resource-leak gate shared by native artifact smoke checks."""
import re


def failed(text):
    return re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', text, re.M) is not None
