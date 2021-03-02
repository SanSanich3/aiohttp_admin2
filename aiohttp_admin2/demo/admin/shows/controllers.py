from aiohttp_admin2.view import ControllerView
from aiohttp_admin2.controllers.postgres_controller import PostgresController
from aiohttp_admin2.mappers.generics import PostgresMapperGeneric
from aiohttp_admin2.controllers.relations import (
    ToManyRelation,
    ToOneRelation,
)

from ...catalog.tables import (
    shows,
    shows_actors,
    shows_genres,
    shows_seasons,

)
from ..actors.controllers import ActorController
from ..genres.controllers import GenresController
from ..images.controller import ImageController
from ..injectors import postgres_injector


class ShowsMapper(PostgresMapperGeneric, table=shows):
    pass


class ActorShowMapper(PostgresMapperGeneric, table=shows_actors):
    pass


class GenreShowsMapper(PostgresMapperGeneric, table=shows_genres):
    pass


class SeasonShowsMapper(PostgresMapperGeneric, table=shows_seasons):
    pass


@postgres_injector.inject
class ShowsController(PostgresController):
    table = shows
    mapper = ShowsMapper
    name = 'shows'
    per_page = 10

    search_fields = ['title', ]
    inline_fields = [
        'poster', 'title', 'status', 'first_air_date', 'last_air_date',
        'vote_average',
    ]

    async def poster_field(self, obj):
        return f'<img ' \
               f'src="https://image.tmdb.org/t/p/w200/{obj.poster_path}"' \
               f'width="100">'

    poster_field.is_safe = True


@postgres_injector.inject
class ActorShowController(PostgresController):
    table = shows_actors
    mapper = ActorShowMapper
    inline_fields = [
        'id', 'poster', 'actor_id', 'actor', 'character', 'order'
    ]
    order_by = 'order'
    list_filter = ['id']

    per_page = 10

    relations_to_one = [
        ToOneRelation(
            name='movie_id',
            field_name='movie_id',
            controller=ShowsController,
        ),
        ToOneRelation(
            name='actor_id',
            field_name='actor_id',
            controller=ActorController,
        ),
    ]

    async def actor_field(self, obj):
        actor = await obj.get_relation('actor_id')
        return actor.name

    async def poster_field(self, obj):
        actor = await obj.get_relation("actor_id")
        return f'<img ' \
               f'src="https://image.tmdb.org/t/p/w200/' \
               f'{actor.url}"' \
               f'width="100">'

    poster_field.is_safe = True


@postgres_injector.inject
class GenreShowController(PostgresController):
    table = shows_genres
    mapper = GenreShowsMapper
    inline_fields = ['id', 'name', ]

    per_page = 10

    relations_to_one = [
        ToOneRelation(
            name='show_id',
            field_name='show_id',
            controller=ShowsController
        ),
        ToOneRelation(
            name='genre_id',
            field_name='genre_id',
            controller=GenresController
        )
    ]

    async def name_field(self, obj) -> str:
        genre = await obj.get_relation('genre_id')
        return genre.name


@postgres_injector.inject
class SeasonShowController(PostgresController):
    table = shows_seasons
    mapper = SeasonShowsMapper
    inline_fields = ['poster', 'season_number', 'episode_count', 'air_date', ]

    per_page = 10

    relations_to_one = [
        ToOneRelation(
            name='show_id',
            field_name='show_id',
            controller=ShowsController
        )
    ]

    async def genre_name_field(self, obj) -> str:
        genre = await obj.get_relation('genre_id')
        return genre.name

    async def poster_field(self, obj):
        return f'<img ' \
               f'src="https://image.tmdb.org/t/p/w200/{obj.poster_path}"' \
               f'width="100">'

    poster_field.is_safe = True


class ShowsPage(ControllerView):
    controller = ShowsController

    relations = [
        ToManyRelation(
            name='Actors_tv',
            left_table_pk='movie_id',
            right_table_pk='actor_id',
            relation_controller=ActorShowController
        ),
        ToManyRelation(
            name='Genres_tv',
            left_table_pk='show_id',
            right_table_pk='genre_id',
            relation_controller=GenreShowController
        ),
        ToManyRelation(
            name='Seasons',
            left_table_pk='show_id',
            right_table_pk='id',
            relation_controller=SeasonShowController
        ),
        ToManyRelation(
            name='ImagesTV',
            left_table_pk='show_id',
            right_table_pk='id',
            relation_controller=ImageController
        ),
    ]

