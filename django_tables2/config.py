# coding: utf-8
from __future__ import unicode_literals

from django.core.paginator import EmptyPage, PageNotAnInteger

SESSION_KEY = "django-tables2"

class RequestConfig(object):
    '''
    A configurator that uses request data to setup a table.

    A single RequestConfig can be used for multiple tables in one view.

    Arguments:
        paginate (dict or bool): Indicates whether to paginate, and if so, what
            default values to use. If the value evaluates to `False`, pagination
            will be disabled. A `dict` can be used to specify default values for
            the call to `~.tables.Table.paginate` (e.g. to define a default
            `per_page` value).

            A special *silent* item can be used to enable automatic handling of
            pagination exceptions using the following logic:

             - If `~django.core.paginator.PageNotAnInteger` is raised, show the first page.
             - If `~django.core.paginator.EmptyPage` is raised, show the last page.

    '''


    def __init__(self, request, paginate=True):
        self.request = request
        self.paginate = paginate

    def _set_session_val(self, key, val):
        if hasattr(self.request, "session"):
            if SESSION_KEY in self.request.session:
                if key not in self.request.session[SESSION_KEY] or self.request.session[SESSION_KEY][key] != val:
                    self.request.session[SESSION_KEY][key] = val
                    self.request.session.modified = True
            else:
                self.request.session[SESSION_KEY] = {key: val}

    def _get_session_val(self, key):
        try:
            return self.request.session[SESSION_KEY][key]
        except (AttributeError, KeyError):
            pass

    def configure(self, table):
        '''
        Configure a table using information from the request.

        Arguments:
            table (`~.Table`): table to be configured
        '''
        order_by = self.request.GET.getlist(table.prefixed_order_by_field)

        if order_by:
            self._set_session_val(table.prefixed_order_by_field, order_by)
        else:
            order_by = self._get_session_val(table.prefixed_order_by_field)

        if order_by:
            table.order_by = order_by

        if self.paginate:
            if hasattr(self.paginate, 'items'):
                kwargs = dict(self.paginate)
            else:
                kwargs = {}

            # extract some options from the request
            try:
                kwargs['page'] = int(self.request.GET[table.prefixed_page_field])
            except (ValueError, KeyError):
                pass

            try:
                kwargs['per_page'] = int(self.request.GET[table.prefixed_per_page_field])
                self._set_session_val(table.prefixed_per_page_field, kwargs['per_page'])
            except (ValueError, KeyError):
                per_page = self._get_session_val(table.prefixed_per_page_field)
                if per_page:
                    kwargs['per_page'] = per_page

            silent = kwargs.pop('silent', True)
            if not silent:
                table.paginate(**kwargs)
            else:
                try:
                    table.paginate(**kwargs)
                except PageNotAnInteger:
                    table.page = table.paginator.page(1)
                except EmptyPage:
                    table.page = table.paginator.page(table.paginator.num_pages)

        return table
