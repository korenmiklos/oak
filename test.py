# -*- coding: utf-8 -*-
import unittest as ut 
import oak as module

from jinja2 import Template
from yamltree import LiteralNode, parse_yaml

class TestRendering(ut.TestCase):
    def setUp(self):
        preview = Template('Preview. T={{title}}.')
        detail = Template('Detail. T={{title}}. C={{content}}')
        children = Template('<ul>{% for item in items %}<li>{{item}}</li>{% endfor %}</ul>')
        branch = module.OakBranch(dict(preview=preview, detail=detail, children=children), 'test')
        title = LiteralNode('title')
        content = LiteralNode('content')

        title.set_data('Title of page')
        content.set_data('Content of page')

        branch.add_child(title)
        branch.add_child(content)

        self.branch = branch
        self.data = {'title': 'Title of page', 'content': 'Content of page'}

    def test_get_dictionary(self):
        self.assertDictEqual(self.branch.get_dictionary(), self.data)

    def test_render_detail_returns_metapage(self):
        self.assertIsInstance(self.branch.render_detail(), module.MetaPage)

    def test_render_detail(self):
        self.assertEqual(self.branch.render_detail().get_data(), 'Detail. T=%s. C=%s' % (self.data['title'], self.data['content']))
        
    def test_render_preview(self):
        self.assertEqual(self.branch.render_preview(), 'Preview. T=%s.' % self.data['title'])

    def test_str(self):
        self.assertEqual(self.branch.render_preview(), str(self.branch))
        


class TestConversion(ut.TestCase):
    def setUp(self):
        self.node = parse_yaml('root', '''
paper1: 
    title: First paper
    content: First content
paper2: 
    title: Second paper
    content: Second content
''')
        templates = dict(preview="{{title}}", detail="Detail. T={{title}}. C={{content}}")
        self.node.set_metadata(templates=dict(detail="<ul>{% for item in current_page %}<li>{{item}}</li>{% endfor %}</ul>"))
        self.node.paper1.set_metadata(templates=templates)
        self.node.paper2.set_metadata(templates=templates)

    def test_returns_branch(self):
        branch = module.yamltree2oakbranch(self.node)
        self.assertIsInstance(branch, module.OakBranch)

    def test_render_root(self):
        branch = module.yamltree2oakbranch(self.node)
        self.assertEqual(branch.render_detail().get_data(), "<ul><li>First paper</li><li>Second paper</li></ul>")

    def test_paper_preview(self):
        branch = module.yamltree2oakbranch(self.node)
        self.assertEqual(str(branch.paper1), "First paper")

    def test_paper_detail(self):
        branch = module.yamltree2oakbranch(self.node)
        self.assertEqual(branch.paper1.render_detail().get_data(), "Detail. T=First paper. C=First content")

if __name__=='__main__':
    ut.main()
