from typing import Optional, Dict, List, Tuple, Union

import aiohttp
from bs4 import BeautifulSoup
import jinja2
import pdfkit

import config
from utils import random_user_agent, get_params
from utils.dict import get_key_by_value


class AsyncParser:
    def __init__(self, filters: Dict[str, Union[str, int]]):
        self._filters = filters
        self._max_page = 0

    async def load_html(self) -> Optional[str]:
        headers = {'User-Agent': random_user_agent.user_agent()}
        session = aiohttp.ClientSession()
        url = get_params.create_url(self._filters)
        resp = await session.get(url, headers=headers)
        text = None
        if resp.status == 200:
            text = await resp.text()
        resp.close()
        await session.close()
        return text

    def get_number_vacancies(self, soup: BeautifulSoup) -> int:
        """Returns the number of vacancies."""
        try:
            text = soup.select('h1[data-qa="bloko-header-1"]')[0].text
            num_vacancies = int(''.join([c for c in text if c.isdigit()]))
        except ValueError:
            num_vacancies = 0
        return num_vacancies

    def set_max_page(self, soup: BeautifulSoup):
        """Sets the maximum page number."""
        pagination = soup.select('div[data-qa="pager-block"]')
        if pagination:
            last_page_with_range = pagination[0].select(
                '.pager-item-not-in-short-range>.pager-item-not-in-short-range>a')  # noqa
            if last_page_with_range:
                self._max_page = int(last_page_with_range[0].text) - 1
            else:
                last_page = pagination[0].select(
                    '.bloko-button-group>span:last-child')
                self._max_page = int(last_page[0].text) - 1

    def get_vacancies(self, soup: BeautifulSoup) -> List[dict]:
        """Returns the vacancies on the page as a list"""
        vacancies = []
        items = soup.select('.vacancy-serp-item')
        for item in items:
            header = item.select('.resume-search-item__name')
            title = header[0].text
            url = header[0].span.a['href']
            salary = item.select('.vacancy-serp-item__sidebar')
            description = item.select(
                'div[data-qa="vacancy-serp__vacancy_snippet_requirement"]')[0].text  # noqa
            vacancy = {
                'title': title,
                'url': url,
                'salary': salary[0].text if salary else '',
                'description': description
            }
            vacancies.append(vacancy)
        return vacancies

    def render_html(self, context: dict) -> str:
        loader = jinja2.FileSystemLoader(searchpath="./templates")
        env = jinja2.Environment(loader=loader)
        template = env.get_template('vacancies.html')
        html = template.render(context)
        return html

    def save_pdf_from_html(self, html: str, pdf_filename: str) -> bool:
        result = pdfkit.from_string(html, pdf_filename)
        return result

    async def save_pdf(self, filename: str) -> Tuple[bool, str]:
        html = await self.load_html()
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            self.set_max_page(soup)
            if self._filters[config.PARAM_HHRU_PAGE] > self._max_page:
                return (False, 'There are no more vacancies')

            offset_indexes = (
                self._filters[config.PARAM_HHRU_PAGE]
                * config.VACANCIES_PER_PAGE
            )
            context = {
                'query': self._filters[config.PARAM_HHRU_QUERY],
                'num_vacancies': self.get_number_vacancies(soup),
                'exp': get_key_by_value(
                    get_params.experience, self._filters[config.PARAM_HHRU_EXP]),  # noqa
                'area': get_key_by_value(
                    get_params.areas, self._filters[config.PARAM_HHRU_AREA]),  # noqa
                'vacancies': self.get_vacancies(soup),
                'offset_indexes': offset_indexes
            }
            html = self.render_html(context)
            result = self.save_pdf_from_html(html, filename)
            return (True, 'Success') if result else (False, 'Error')
        else:
            return (False, 'Error')
