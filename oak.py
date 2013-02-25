#!/usr/bin/env python
# encoding: utf-8

'''
'''


__docformat__ = 'markdown en'
__author__ = "Miklós Koren <miklos.koren@gmail.com>"
__version__ = "0.1.0"

import re
import os.path
from yamltree import ContainerNode, LiteralNode, YAMLTree
from jinja2 import FileSystemLoader, Template
from jinja2.environment import Environment

def mock():
    tmpl = env.get_template('page.html')
    print tmpl.render(parser.vars)

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

def yamltree2oakbranch(node):
    if isinstance(node, LiteralNode):
        # literal is not branch, stop recursion
        # make a shallow copy so as to not violate single parent restriction
        newnode = LiteralNode(node.__name__)
        newnode.set_data(node.get_data())
        return newnode
    elif isinstance(node, ContainerNode):
        templates = {}
        for (key, value) in node.__meta__['templates'].items():
            templates[key] = Template(value)
        branch = OakBranch(templates, node.__name__)
        for child in node:
            # convert all children to branches
            branch.add_child(yamltree2oakbranch(child))
        return branch

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


class OakBranch(ContainerNode):
    '''
    A subtree of webpages.
    '''
    def __init__(self, templates, *args):
        super(OakBranch, self).__init__(*args)
        self.set_metadata(templates=templates)

    def render_preview(self):
        return self.get_metadata('templates')['preview'].render(**self.get_dictionary())

    def render_detail(self):
        '''
        Render the page. `current_page` is a YAMLTree node corresponding to this page. 
        Children of the node are also made available directly as local variables, so that
        `current_page.title` and `title` mean exactly the same.
        '''
        data = self.children_as_dictionary()
        data['current_page'] = self
        page = MetaPage('index.html', 
            self.get_metadata('templates')['detail'].render(**data),
            path=self.get_absolute_url())
        return page

    def __unicode__(self):
        return self.render_preview()

    def __str__(self):
        return self.__unicode__()

if __name__=='__main__':
    env = Environment()
    env.loader = FileSystemLoader('site/templates')
    root = YAMLTree('site/content')

    pages = render_all_pages(env, root)
    for page in pages:
        print os.path.join(page.get_metadata('path'), page.__name__)+page.get_metadata('extension')
        print page

