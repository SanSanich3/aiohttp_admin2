import typing as t

import aiohttp_jinja2
from aiohttp import web

from .tab_template_view import TabTemplateView
from aiohttp_admin2.controllers.controller import (
    Controller,
    DETAIL_NAME,
    FOREIGNKEY_DETAIL_NAME,
)
from aiohttp_admin2.resources.types import Instance
from aiohttp_admin2.resources.types import FilterTuple
from aiohttp_admin2.view.aiohttp.views.utils import ViewUtilsMixin
from aiohttp_admin2.mappers import Mapper


__all__ = ['ManyToManyTabView', ]


# todo: nested from controller
class ManyToManyTabView(ViewUtilsMixin, TabTemplateView):
    controller: Controller
    template_detail_create_name = 'aiohttp_admin/layouts/create_page.html'
    template_detail_name = 'aiohttp_admin/layouts/detail_edit_page.html'
    template_name: str = 'aiohttp_admin/layouts/list_page.html'
    left_table_name: str
    right_table_name: str

    def get_extra_media(self):
        css = []
        js = []

        for w in {
            **self.default_type_widgets,
            **self.type_widgets,
            **self.fields_widgets,
        }.values():
            css.extend([link for link in w.css_extra if link not in css])
            js.extend([link for link in w.js_extra if link not in js])

        return dict(css=css, js=js)

    def get_controller(self) -> Controller:
        return self.controller.builder_form_params({})

    @property
    def create_url_name(self):
        return self.index_url_name + '_create'

    @property
    def create_post_url_name(self):
        return self.index_url_name + '_create_post'

    @property
    def update_post_url_name(self):
        return self.index_url_name + '_update_post'

    @property
    def delete_url_name(self):
        return self.index_url_name + '_delete'

    @property
    def detail_url_name(self):
        return self.index_url_name + '_detail'

    def get_autocomplete_url(self, name: str) -> str:
        return f'/{self.index_url_name}/_autocomplete_{name}'

    def get_autocomplete_url_name(self, name: str) -> str:
        return f'{self.index_url_name}_autocomplete_{name}'

    def setup(self, app: web.Application) -> None:
        controller = self.get_controller()
        app.add_routes([
            web.get(self.index_url, self.get_list, name=self.index_url_name),
            web.get(self.index_url + '/create', self.get_create, name=self.create_url_name),
            web.post(self.index_url + '/create_post', self.post_create, name=self.create_post_url_name),
            web.post(self.index_url + '/update/{nested_pk:\w+}', self.post_update, name=self.update_post_url_name),
            web.get(self.index_url + '/detail/{nested_pk:\w+}', self.get_detail, name=self.detail_url_name),
            web.post(self.index_url + '/detail/{nested_pk:\w+}', self.post_delete, name=self.delete_url_name),
        ])

        # autocomplete
        autocomplete_routes = []
        for name, relation in controller.foreign_keys_field_map.items():
            inner_controller = relation.controller()

            async def autocomplete(req):

                res = await inner_controller\
                    .get_autocomplete_items(
                        text=req.rel_url.query.get('q'),
                        page=int(req.rel_url.query.get('page', 1)),
                    )

                return web.json_response(res)

            autocomplete_routes.append(web.get(
                self.get_autocomplete_url(name),
                autocomplete,
                name=self.get_autocomplete_url_name(name)
            ))

        app.add_routes(autocomplete_routes)

    async def get_create(
        self,
        req: web.Request,
        mapper: t.Dict[str, t.Any] = None,
    ) -> web.Response:
        controller = self.get_controller()
        pk = req.match_info['pk']

        return aiohttp_jinja2.render_template(
            self.template_detail_create_name,
            req,
            {
                **await self.get_context(req),
                "media": self.get_extra_media(),
                "controller": controller,
                "title": f"Create a new {self.name}",
                "mapper": mapper or controller.mapper({
                    self.left_table_name: self.get_pk(req)
                }),
                "fields": controller.fields,
                "exclude_fields": self.controller.exclude_create_fields,
                "create_post_url": req.app.router[self.create_post_url_name]
                    .url_for(pk=pk)
            }
        )

    async def post_create(self, req: web.Request) -> web.Response:
        controller = self.get_controller()
        data = dict(await req.post())

        obj = await controller.create(data)

        if isinstance(obj, Mapper):
            return await self.get_create(req, obj)
        else:
            raise web.HTTPFound(
                req.app.router[self.index_url_name]
                    .url_for(pk=self.get_pk(req))
                    .with_query(
                    f'message=The {self.name}#{obj.id} has been created'
                )
            )

    async def post_update(self, req: web.Request) -> web.Response:
        controller = self.get_controller()
        data = dict(await req.post())
        pk = req.match_info['pk']
        nested_pk = req.match_info['nested_pk']

        obj = await controller.update(nested_pk, data)

        if isinstance(obj, Mapper):
            return await self.get_detail(req, obj)
        else:
            raise web.HTTPFound(
                req.app.router[self.detail_url_name]
                    .url_for(pk=pk, nested_pk=nested_pk)
                    .with_query(
                    f'message=The {self.name}#{nested_pk} has been updated'
                )
            )

    async def get_list(self, req: web.Request) -> web.Response:
        params = self.get_params_from_request(req)
        controller = self.get_controller()
        filters_list = self.get_list_filters(
            req,
            controller,
            self.default_filter_map,
        )
        filters_list.append(FilterTuple(
            self.left_table_name,
            self.get_pk(req),
            'eq',
        ))

        def url_builder(obj: Instance, url_type: str, **kwargs) -> str:
            if url_type is DETAIL_NAME:
                return str(
                    req.app.router[self.detail_url_name]
                    .url_for(
                        nested_pk=str(obj.get_pk()),
                        pk=req.match_info['pk']
                    )
                )
            elif url_type is FOREIGNKEY_DETAIL_NAME:
                url_name = kwargs.get('url_name')
                return str(
                    req.app.router[url_name + '_detail']
                        .url_for(
                            pk=str(obj.get_pk())
                        )
                    )

            return ''

        data = await controller.get_list(
            **params._asdict(),
            filters=filters_list,
            url_builder=url_builder,
        )

        return aiohttp_jinja2.render_template(
            self.template_name,
            req,
            {
                **await self.get_context(req),
                'title': f"{self.parent.name}#{self.get_pk(req)}",
                'list': data,
                'content': await self.get_content(req),
                "controller": controller,
                "tabs": self.parent.tabs_list,
                "detail_url": req.app.router[self.parent.detail_url_name]
                    .url_for(pk=req.match_info['pk']),
                "create_url": req.app.router[self.create_url_name]
                    .url_for(pk=req.match_info['pk']),
                "view_filters": self.get_filters(req.rel_url.query),
            },
        )

    async def get_detail(
        self,
        req: web.Request,
        mapper: t.Dict[str, t.Any] = None,
    ) -> web.Response:
        controller = self.get_controller()
        pk = req.match_info['pk']
        nested_pk = req.match_info['nested_pk']
        data = await controller.get_detail(req.match_info['nested_pk'])

        return aiohttp_jinja2.render_template(
            self.template_detail_name,
            req,
            {
                **await self.get_context(req),
                "object": data,
                "media": self.get_extra_media(),
                "exclude_fields": self.controller.exclude_update_fields,
                "controller": controller,
                "title": f"{self.name}#{data.id}",
                "pk": self.get_pk(req),
                "nested_pk": req.match_info['nested_pk'],
                "delete_url": req.app.router[self.delete_url_name]
                    .url_for(pk=pk, nested_pk=nested_pk),
                "detail_url": req.app.router[self.detail_url_name]
                    .url_for(pk=pk, nested_pk=nested_pk),
                "save_url": req.app.router[self.update_post_url_name]
                    .url_for(pk=pk, nested_pk=nested_pk),
                "mapper": mapper or controller.mapper(data.__dict__),
                "fields": controller.fields,
            }
        )

    async def post_delete(self, req: web.Request) -> None:
        controller = self.get_controller()
        pk = req.match_info['nested_pk']
        await controller.delete(int(pk))
        location = req.app.router[self.index_url_name] \
            .url_for(pk=self.get_pk(req)) \
            .with_query(f'message=The {self.name}#{pk} has been deleted')
        raise web.HTTPFound(location=location)
