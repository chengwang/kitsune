import cgi
import urlparse

from django.core.urlresolvers import reverse
from django.utils.datastructures import MultiValueDict

import jinja2

from jingo import register, env
from flatqs import flatten


@register.filter
def paginator(pager):
    return Paginator(pager).render()


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)


@register.filter
def urlparams(url_, hash=None, **query):
    """
    Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    query_dict = MultiValueDict()
    if url.query:
        for k, v in cgi.parse_qsl(url.query):
            query_dict.update({k: v})
    for k, v in query.items():
        query_dict.update({k: v})

    query_string = flatten(query_dict, encode=False)
    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return jinja2.Markup(new.geturl())


class Paginator(object):

    def __init__(self, pager):
        self.pager = pager

        self.max = 10
        self.span = (self.max - 1) / 2

        self.page = pager.number
        self.num_pages = pager.paginator.num_pages
        self.count = pager.paginator.count

        pager.page_range = self.range()
        pager.dotted_upper = self.num_pages not in pager.page_range
        pager.dotted_lower = 1 not in pager.page_range

    def range(self):
        """Return a list of page numbers to show in the paginator."""
        page, total, span = self.page, self.num_pages, self.span
        if total < self.max:
            lower, upper = 0, total
        elif page < span + 1:
            lower, upper = 0, span * 2
        elif page > total - span:
            lower, upper = total - span * 2, total
        else:
            lower, upper = page - span, page + span - 1
        return range(max(lower + 1, 1), min(total, upper) + 1)

    def render(self):
        c = {'pager': self.pager, 'num_pages': self.num_pages,
             'count': self.count}
        t = env.get_template('layout/paginator.html').render(**c)
        return jinja2.Markup(t)


@register.filter
def fe(str, *args, **kwargs):
    """Format a safe string with potentially unsafe arguments, then return a
    safe string."""

    for i in kwargs:
        kwargs[i] = jinja2.escape(kwargs[i])

    return jinja2.Markup(str.format(**kwargs))