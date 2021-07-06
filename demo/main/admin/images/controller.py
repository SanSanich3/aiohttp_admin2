from markupsafe import Markup
from aiohttp_admin2.controllers.postgres_controller import PostgresController
from aiohttp_admin2.mappers.generics import PostgresMapperGeneric

from ...catalog.tables import images_links
from ..injectors import postgres_injector


class ImageMapper(PostgresMapperGeneric, table=images_links):
    pass


@postgres_injector.inject
class ImageController(PostgresController, table=images_links):
    mapper = ImageMapper
    name = 'images'
    per_page = 10

    inline_fields = ['photo', 'type', ]

    async def photo_field(self, obj):
        return Markup(
                '<img'
                '   src="https://image.tmdb.org/t/p/w200/{path}"'
                '   width="100"'
                ' />'
            )\
            .format(path=obj.data.url)
