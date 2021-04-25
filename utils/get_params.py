"""
Creates a URL to search jobs on specific filters.
"""

from typing import Dict, Union

import config

experience = {
    'No': 'noExperience',
    '1-3': 'between1And3',
    '3-6': 'between3And6',
    'More 6': 'moreThan6'
}

areas = {
    'Moscow': '1',
    'StPetersburg': '2',
    'Krasnodar': '53'
}


def create_url(filters: Dict[str, Union[str, int]]):
    url = '{}?{}={}&{}={}&{}={}&{}={}'.format(
        config.URL_JOB_SEARCH_HHRU,
        config.PARAM_HHRU_QUERY,
        filters[config.PARAM_HHRU_QUERY].replace(' ', '+'),
        config.PARAM_HHRU_EXP,
        filters[config.PARAM_HHRU_EXP],
        config.PARAM_HHRU_AREA,
        filters[config.PARAM_HHRU_AREA],
        config.PARAM_HHRU_PAGE,
        filters[config.PARAM_HHRU_PAGE]
    )
    return url
