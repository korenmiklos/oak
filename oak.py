#!/usr/bin/env python
# encoding: utf-8

'''
'''


__docformat__ = 'markdown en'
__author__ = "Miklós Koren <miklos.koren@gmail.com>"
__version__ = "0.1.0"

import re
import os.path
import shutil
from yamltree import ContainerNode, LiteralNode, YAMLTree
from jinja2 import FileSystemLoader, Template
from jinja2.environment import Environment

def get_nodes_for_template(root, name):
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
            parent = root.get_by_url(parts[0])
            dct = {}
            for child in parent:
                dct[parts[0]+child.__name__+parts[1]] = child
            return dct
    else:
        try:
            # first find data based on full template name without extension
            return {name: root.get_by_url(os.path.join(head,base))}
        except LookupError :
            try:
                # then find data based on template path alone
                return {name: root.get_by_url(head)}
            except LookupError:
                return {name: root}

def render_to_metapage(env, name, root):
    template = env.get_template(name)
    nodes = get_nodes_for_template(root, name)
    pages = []
    for filename, node in nodes.iteritems():
        # get parts of filename
        path, fname = os.path.split(filename)
        # fill template with data
        data = node.children_as_dictionary()
        data['current_page'] = node
        if root is not None:
            data['site_root'] = root
        pages.append(MetaPage(fname, template.render(**data), path=path))
    return pages

def render_all_pages(env, root):
    pages = []
    for name in env.list_templates():
        pages.extend(render_to_metapage(env, name, root))
    return pages

class MetaPage(object):
    '''
    Unicode string of a page content with metadata: name, path etc. 
    '''
    def __init__(self, name, content, path='', encoding='utf-8'):
        self.path = path
        self.name = name
        self.content = unicode(content)
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
        output.write(self.content.encode(self.encoding))
        output.close()

class OakSite(object):
    '''
    An Oak website.
    '''
    def __init__(self, root='.', templates=None, content=None, output=None):
        if templates is None:
            templates = os.path.join(root, 'templates')
        if content is None:
            content = os.path.join(root, 'content')
        if output is None:
            output = os.path.join(root, 'output')

        self.environment = Environment()
        self.environment.loader = FileSystemLoader(templates)
        self.data = YAMLTree(content)
        self.output = output

    def generate(self):
        '''
        Render and save all pages.
        '''
        pages = render_all_pages(self.environment, self.data)
        for page in pages:
            page.save(self.output)

    def clean(self):
        '''
        Remove all files in output foled.
        '''
        shutil.rmtree(self.output)
        os.makedirs(self.output)


