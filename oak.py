#!/usr/bin/env python
# encoding: utf-8

'''
'''


__docformat__ = 'markdown en'
__author__ = "Miklós Koren <miklos.koren@gmail.com>"
__version__ = "0.1.0"

import re
from yamltree import ContainerNode, LiteralNode
from jinja2 import Template


def yamltree2oakbranch(node):
    if isinstance(node, LiteralNode):
        # literal is not branch, stop recursion
        return node
    elif isinstance(node, ContainerNode):
        templates = {}
        for (key, value) in node.__meta__['templates'].items():
            templates[key] = Template(value)
        branch = OakBranch(templates, node.__name__)
        for child in node:
            # convert all childreb to branches
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
        page = MetaPage(self.__name__, self.get_metadata('templates')['detail'].render(**data))
        return page

    def __unicode__(self):
        return self.render_preview()

    def __str__(self):
        return self.__unicode__()
