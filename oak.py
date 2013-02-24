#!/usr/bin/env python
# encoding: utf-8

'''
'''


__docformat__ = 'markdown en'
__author__ = "Miklós Koren <miklos.koren@gmail.com>"
__version__ = "0.1.0"

import re
import os.path
from yamltree import ContainerNode, LiteralNode
from jinja2 import FileSystemLoader, Template
from jinja2.environment import Environment

def mock():
    env = Environment()
    env.loader = FileSystemLoader('.')
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
            return dict(name=root.get_by_url(os.path.join(head,base)))
        except LookupError :
            try:
                # then find data based on template path alone
                return dict(name=root.get_by_url(head))
            except LookupError:
                return dict(name=root)

def render_to_metapage(node, template):
    pass

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

class MetaPage(LiteralNode):
    '''
    String of a page content with metadata: name, path etc. 
    For convenience, it is subclassed from LiteralNode.
    '''
    def __init__(self, name, content, path='', extension='html', encoding='utf-8'):
        super(MetaPage, self).__init__(name=name)
        self.set_data(content)
        self.set_metadata(path=path, extension=extension, encoding=encoding)


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
        page = MetaPage('index', 
            self.get_metadata('templates')['detail'].render(**data),
            path=self.get_absolute_url(),
            extension='html')
        return page

    def __unicode__(self):
        return self.render_preview()

    def __str__(self):
        return self.__unicode__()
