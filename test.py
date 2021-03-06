# -*- coding: utf-8 -*-
import unittest as ut 
import oak as module
import os
from shutil import rmtree

from jinja2 import Template, Environment, DictLoader
from datatree import LiteralNode, DataTree
import yaml

class TestFilters(ut.TestCase):
    def test_limit(self):
        self.assertListEqual(module.limit_filter([1, 2, 3, 4, 5], 2), [1, 2])

    def test_rst(self):
        self.assertEqual(module.rst_filter('*strong*'), '<p><em>strong</em></p>\n')

    def test_number(self):
        self.assertEqual(module.number_filter('2.266e-02'), '0.02')
        self.assertEqual(module.number_filter('2.266e-02', format='{:.3f}'), '0.023')

    def test_where(self):
        self.assertListEqual(module.where_filter([
            dict(a=1,cucc=2),
            dict(a=2,cucc=1),
            dict(a=3,cucc=1)], 'cucc=1'), 
            [dict(a=2,cucc=1),dict(a=3,cucc=1)])

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
            'Root={{site_root.__name__}}. Meta={{META.TITLE}}. Page={{current_page.__name__}}'})
        os.makedirs('testdata/parent')
        doc0 = open('testdata/meta.yaml', 'w')
        doc1 = open('testdata/parent/child.yaml', 'w')
        data = dict(title='Test document', content='Test data')
        
        for stream in [doc0, doc1]:
            yaml.dump(data, stream)
            stream.close()

        self.data = DataTree('testdata')

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
        self.assertEqual(page[0].get_data(), 'Root=testdata. Meta=Test document. Page=child')

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

    def test_excluded_template(self):
        site = module.OakSite(root='testdata', excluded_templates='folder2/.*')
        site.generate()
        for page in ['testdata/output/folder2/document.html']:
            self.failIf(os.path.isfile(page))

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

        self.node = DataTree('testdata')

    def tearDown(self):
        rmtree('testdata')

    def test_no_leading_slash(self):
        self.assertEqual(module.get_nodes_for_template(self.node, 'folder1/index.html').values()[0], self.node.root.folder1)

    def test_index_html(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1/index.html').values()[0], self.node.root.folder1)

    def test_two_deep(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1/document/index.html').values()[0], self.node.root.folder1.document)

    def test_reverse_url(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1/document/index.html').values()[0].get_absolute_url(), '/folder1/document')

    def test_paper1_html(self):
        self.assertEqual(module.get_nodes_for_template(self.node, '/folder1.html').values()[0], self.node.root.folder1)

    def test_unknown_html(self):
        self.assertDictEqual(module.get_nodes_for_template(self.node, '/paper3.html'), {'/paper3.html': self.node.root})

    def test_children(self):
        nodes = {'/folder2/index.html': self.node.get_by_url('/folder2'),
            '/folder1/index.html': self.node.get_by_url('/folder1'),
            '/document/index.html': self.node.get_by_url('/document'),
            }
        self.assertDictEqual(module.get_nodes_for_template(self.node, '/_children/index.html'), nodes)

    def test_grand_children(self):
        nodes = {'/folder2/document.html': self.node.get_by_url('/folder2/document'),
            '/folder1/document.html': self.node.get_by_url('/folder1/document'),
            '/document/title.html': self.node.get_by_url('/document/title'),
            '/document/content.html': self.node.get_by_url('/document/content'),
            }
        self.assertDictEqual(module.get_nodes_for_template(self.node, '/_children/_children.html'), nodes)

    def test_children_html(self):
        nodes = {'/folder1/document.html': self.node.get_by_url('/folder1/document')}
        self.assertDictEqual(module.get_nodes_for_template(self.node, '/folder1/_children.html'), nodes)

if __name__=='__main__':
    ut.main()
