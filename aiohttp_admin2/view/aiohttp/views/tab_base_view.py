import typing as t

from aiohttp import web
from abc import abstractmethod

from aiohttp_admin2.view.aiohttp.utils import get_field_value

__all__ = ['TabBaseView', ]


class TabBaseView:
    name: str

    def __init__(self, parent):
        self.parent = parent

    async def get_context(self, req: web.Request) -> t.Dict[str, t.Any]:
        return {
            'request': req,
            'controller_view': self,
            'parent': self.parent,
            'pk': req.match_info['pk'],
            "message": req.rel_url.query.get('message'),
            "get_field_value": get_field_value,
            "url_query": req.rel_url.query,
            "url_path": req.rel_url.path,
        }

    @abstractmethod
    def setup(self, app: web.Application) -> None: ...

    @property
    def index_url_name(self) -> str:
        return f'{self.__class__.name}_{self.name}'

    @property
    def index_url(self) -> str:
        return f'{self.parent.index_url}' + r'{pk:\w+}' + f'/{self.name}'
