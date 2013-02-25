# -*- coding: utf-8 -*-
import unittest as ut 
import oak as module
import os
from shutil import rmtree

from jinja2 import Template, Environment, DictLoader
from yamltree import LiteralNode, parse_yaml, YAMLTree
import yaml

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
        
class TestMetaPage(ut.TestCase):
    def setUp(self):
        os.makedirs('testdata')

    def test_save_path(self):
        page = module.MetaPage('index.html', 'string', 'testdata/folder')
        page.save()
        self.failUnless(os.path.isfile('testdata/folder/index.html'))

    def test_save_relative_path(self):
        page = module.MetaPage('index.html', 'string', 'folder')
        page.save(root='testdata')
        self.failUnless(os.path.isfile('testdata/folder/index.html'))

    def test_save_content(self):
        page = module.MetaPage('index.html', 'String', 'testdata/folder')
        page.save()
        self.assertEqual(open('testdata/folder/index.html', 'r').read(), 'String')

    def test_save_encoding(self):
        page = module.MetaPage('index.html', u'árvíztűrő tükörfúrógép', 'testdata/folder', encoding='utf-8')
        page.save()
        self.assertEqual(open('testdata/folder/index.html', 'r').read().decode('utf-8'), u'árvíztűrő tükörfúrógép')

    def tearDown(self):
        rmtree('testdata')

class TestRenderToMetaPage(ut.TestCase):
    def setUp(self):
        try:
            rmtree('testdata')
        except:
            pass
        self.env = Environment()
        self.env.loader = DictLoader({'parent/child/index.html': 
            'Root={{site_root.__name__}}. Page={{current_page.__name__}}'})
        os.makedirs('testdata/parent')
        doc0 = open('testdata/parent/child.yaml', 'w')
        data = dict(title='Test document', content='Test data')
        
        for stream in [doc0]:
            yaml.dump(data, stream)
            stream.close()

        self.data = YAMLTree('testdata')

    def tearDown(self):
        rmtree('testdata')

    def test_render_name(self):
        page = module.render_to_metapage(self.env, 'parent/child/index.html', self.data)
        self.assertEqual(page[0].name, 'index.html')

    def test_render_path(self):
        page = module.render_to_metapage(self.env, 'parent/child/index.html', self.data)
        self.assertEqual(page[0].path, 'parent/child')

    def test_render_content(self):
        page = module.render_to_metapage(self.env, 'parent/child/index.html', self.data)
        self.assertEqual(page[0].get_data(), 'Root=root. Page=child')

class TestOakSite(ut.TestCase):
    def setUp(self):
        try:
            rmtree('testdata')
        except:
            pass
        # data
        os.makedirs('testdata/content/folder1')
        os.makedirs('testdata/content/folder2')
        doc0 = open('testdata/content/document.yaml', 'w')
        doc1 = open('testdata/content/folder1/document.yaml', 'w')
        doc2 = open('testdata/content/folder2/document.yaml', 'w')
        data = dict(title='Test document', content='Test data')
        
        for stream in [doc0, doc1, doc2]:
            yaml.dump(data, stream)
            stream.close()

        # templates
        os.makedirs('testdata/templates/folder1')
        os.makedirs('testdata/templates/folder2')
        doc0 = open('testdata/templates/document.html', 'w')
        doc1 = open('testdata/templates/folder1/document.html', 'w')
        doc2 = open('testdata/templates/folder2/document.html', 'w')
        
        for stream in [doc0, doc1, doc2]:
            stream.write('{{title}}')
            stream.close()

    def tearDown(self):
        rmtree('testdata')

    def test_default_site(self):
        site = module.OakSite(root='testdata')
        site.generate()
        for page in ['testdata/output/document.html',
                     'testdata/output/folder1/document.html',
                     'testdata/output/folder2/document.html']:
            self.failUnless(os.path.isfile(page))

    def test_site_content(self):
        site = module.OakSite(root='testdata')
        site.generate()
        for page in ['testdata/output/document.html',
                     'testdata/output/folder1/document.html',
                     'testdata/output/folder2/document.html']:
            self.assertEqual(open(page, 'r').read(), 'Test document')


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

    def test_paper_detail_url(self):
        branch = module.yamltree2oakbranch(self.node)
        page = branch.paper1.render_detail()
        self.assertEqual(os.path.join(page.path, page.name),
            '/paper1/index.html')

class TestNodesForTemplate(ut.TestCase):
    def setUp(self):
        os.makedirs('testdata/folder1')
        os.makedirs('testdata/folder2')
        doc0 = open('testdata/document.yaml', 'w')
        doc1 = open('testdata/folder1/document.yaml', 'w')
        doc2 = open('testdata/folder2/document.yaml', 'w')
        data = dict(title='Test document', content='Test data')
        
        for stream in [doc0, doc1, doc2]:
            yaml.dump(data, stream)
            stream.close()

        self.node = YAMLTree('testdata')

    def tearDown(self):
        rmtree('testdata')

    def test_no_leading_slash(self):
        self.assertEqual(module.get_nodes_for_template(self.node, 'folder1/index.html').values()[0], self.node.folder1)

    def test_index_html(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1/index.html').values()[0], self.node.folder1)

    def test_two_deep(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1/document/index.html').values()[0], self.node.folder1.document)

    def test_reverse_url(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1/document/index.html').values()[0].get_absolute_url(), '/folder1/document')

    def test_paper1_html(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1.html').values()[0], self.node.folder1)

    def test_unknown_html(self):
        self.assertDictEqual(module.get_nodes_for_template(self.node, '/paper3.html'), {'/paper3.html': self.node})

    def test_children(self):
        nodes = {'/folder2/index.html': self.node.get_by_url('/folder2'),
            '/folder1/index.html': self.node.get_by_url('/folder1'),
            '/document/index.html': self.node.get_by_url('/document'),
            }
        self.assertDictEqual(module.get_nodes_for_template(self.node, '/_children/index.html'), nodes)

    def test_children_html(self):
        nodes = {'/folder1/document.html': self.node.get_by_url('/folder1/document')}
        self.assertDictEqual(module.get_nodes_for_template(self.node, '/folder1/_children.html'), nodes)

if __name__=='__main__':
    ut.main()
