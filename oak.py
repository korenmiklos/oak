#!/usr/bin/env python
# encoding: utf-8

from math import exp

'''
'''


__docformat__ = 'markdown en'
__author__ = "Miklós Koren <miklos.koren@gmail.com>"
__version__ = "0.2.4"

import re
import os.path
import shutil
import time
from datatree import ContainerNode, LiteralNode, DataTree
from jinja2 import FileSystemLoader, Template, Markup
from jinja2.environment import Environment

from docutils.core import publish_parts

def author_filter(text):
    if isinstance(text, str):
        data = text
    elif isinstance(text, LiteralNode):
        data = text.get_data()
    else:
        data = text
    authors = data.split(', ')
    if len(authors) == 1:
        authors = data.split(' and ')
        if len(authors) > 1:
            authors[1] = ' and ' + authors[1]
    first_author_names = authors[0].split()
    authors[0] = '{}, {}'.format(first_author_names[-1], ' '.join(first_author_names[0:-1]))
    return ', '.join(authors)

def limit_filter(iterable, max=10):
    lst = []
    for item in iterable:
        if len(lst)<max:
            lst.append(item)
        else:
            break
    return lst

def float_filter(text):
    if isinstance(text, str):
        data = float(text)
    elif isinstance(text, LiteralNode):
        try:
            data = float(text.get_data())
        except:
            raise ValueError(text.get_absolute_url())
    else:
        data = float(text)
    return data

def number_filter(text, format=None):
    if isinstance(text, str):
        data = float(text)
    elif isinstance(text, LiteralNode):
        try:
            data = float(text.get_data())
        except:
            raise ValueError(text.get_absolute_url())
    else:
        data = float(text)
    if format is None:
        # sensible number format choices
        format = "{:.2f}"
        if abs(data)<1:
            format = "{:.3f}"
        if abs(data)>=100:
            format = "{:,.0f}"
    return format.format(data)

def percentage_filter(text, format=None):
    if isinstance(text, str):
        data = float(text)
    elif isinstance(text, LiteralNode):
        data = float(text.get_data())
    else:
        data = float(text)
    data = exp(data)*100-100
    return number_filter(data, format)

def where_filter(iterable, condition):
    # absolute simples condition parser
    field, value = condition.split('=')
    return [item for item in iterable if (item[field.strip()])==(value.strip())]

def rst_filter(text):
    if isinstance(text, str):
        data = text
    elif isinstance(text, LiteralNode):
        data = text.get_data()
    else:
        data = text
    return publish_parts(source=data, writer_name='html')['body']

def monthyear(value):
    return time.strftime('%B %Y', time.strptime(value.get_data(), '%Y-%m-%d'))

def datetime(value):
    return time.strptime(value.get_data(), '%Y-%m-%d')

def get_nodes_for_template(tree, name):
    '''
    Given a template name, return a dictionary of fitting data nodes. 
    '''
    head, tail = os.path.split(name)
    forehead, neck = os.path.split(head)
    base, ext = os.path.splitext(tail)
    if (neck=='_children') or (base=='_children'):
        # look for children template
        parts = name.split('_children')
        if len(parts)>1:
            # parent node
            parent = tree.get_by_url(parts[0])
            dct = {}
            for child in parent:
                child_name = parts[0]+child.__name__+"_children".join(parts[1:])
                # check for grandchildren
                dct.update(get_nodes_for_template(tree, child_name))
            return dct
    else:
        try:
            # first find data based on full template name without extension
            return {name: tree.get_by_url(os.path.join(head,base))}
        except LookupError :
            try:
                # then find data based on template path alone
                return {name: tree.get_by_url(head)}
            except LookupError:
                return {name: tree.root}

def render_to_metapage(env, name, tree):
    template = env.get_template(name)
    nodes = get_nodes_for_template(tree, name)
    pages = []
    for filename, node in nodes.items():
        # get parts of filename
        path, fname = os.path.split(filename)
        # fill template with data
        data = node.children_as_dictionary()
        data['current_page'] = node
        if tree.root is not None:
            data['site_root'] = tree.root
            # also add root variables with UPPERCASE
            for variable in tree.root:
                data[variable.__name__.upper()] = variable
        pages.append(MetaPage(fname, template.render(**data), path=path))
    return pages

def render_all_pages(env, tree, exclude=[]):
    pages = []
    for name in env.list_templates():
        if not any([pattern.match(name) for pattern in exclude]):
            print('Rendering %s' % name)
            pages.extend(render_to_metapage(env, name, tree))
    return pages

class MetaPage(object):
    '''
    Unicode string of a page content with metadata: name, path etc. 
    '''
    def __init__(self, name, content, path='', encoding='utf-8'):
        self.path = path
        self.name = name
        self.content = content
        self.encoding = encoding

    def get_data(self):
        return self.content

    def save(self, root='.'):
        '''
        Write out page to file system.
        '''
        fullpath = os.path.join(root, self.path)
        if not os.path.isdir(fullpath):
            os.makedirs(fullpath)
        output = open(os.path.join(fullpath, self.name), 'w')
        output.write(self.content)
        output.close()

class OakSite(object):
    '''
    An Oak website.
    '''
    def __init__(self, root='.', templates=None, content=None, output=None, 
        excluded_templates=[], primary_keys=[]):
        if templates is None:
            templates = os.path.join(root, 'templates')
        if content is None:
            content = os.path.join(root, 'content')
        if output is None:
            output = os.path.join(root, 'output')
        if isinstance(excluded_templates, str):
            excluded_templates = [excluded_templates]

        self.environment = Environment()
        self.environment.filters['author'] = author_filter
        self.environment.filters['number'] = number_filter
        self.environment.filters['percentage'] = percentage_filter
        self.environment.filters['rst'] = rst_filter
        self.environment.filters['limit'] = limit_filter
        self.environment.filters['filter'] = where_filter
        self.environment.filters['monthyear'] = monthyear
        self.environment.filters['datetime'] = datetime
        self.environment.loader = FileSystemLoader(templates)
        self.datatree = DataTree(content, primary_keys=primary_keys)
        self.output = output
        self.excluded_templates = [re.compile(pattern) for pattern in excluded_templates]

    def generate(self):
        '''
        Render and save all pages.
        '''
        # clean folders first
        # self.clean()
        pages = render_all_pages(self.environment, self.datatree, self.excluded_templates)
        for page in pages:
            page.save(self.output)

    def clean(self):
        '''
        Remove all files in output foled.
        '''
        shutil.rmtree(self.output)
        os.makedirs(self.output)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('root', help='Root folder of the site')
    parser.add_argument('-c', '--content', help='Path of content folder. Default is root/content')
    parser.add_argument('-o', '--output', help='Path of output folder. Default is root/output')
    parser.add_argument('-t', '--templates', help='Path of template folder. Default is root/templates')
    parser.add_argument('-x', '--exclude', help='A regular expression for templates to exlude from rendering.')
    parser.add_argument('-p', '--primarykey', help='A field holding primary keys for list items. Default is id#.')
    args = parser.parse_args()

    if args.exclude is None:
        args.exclude = []
    if args.primarykey is None:
        args.primarykey = []

    site = OakSite(args.root, content=args.content, 
        templates=args.templates, output=args.output, 
        excluded_templates=args.exclude,
        primary_keys=args.primarykey)
    print('Generating site...')
    site.generate()