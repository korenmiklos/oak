Oak
===

Oak is a static website generator for hierarchical (tree-structured) data. It uses [YAMLTree][] for datastore and [Jinja2][] for templating.

Why Oak?
--------

Some sites, such as blogs, change often but have little structure. These are well served by static website generators that render HTML pages from markdown. Others have a lot of structure and also change frequently. These need a content management system.

Oak is for sites that have a lot of structure but do not change frequently. For example, a personal collection of research papers may look like:

	papers
		published
			paper1.yaml
				title: A Treatise on Family
				author: Gary Becker
			paper2.yaml

Oak will render this into `papers/published/paper.html` etc.

Guiding principles
------------------

If the structure of your websote follows the structure of your data closely, Oak can render your website in five minutes with the default options. For more complex websites, you can tweak Oak as much as you like using the Jinja2 templating language.

Any website generator should

1. read data from a datastore,
2. render data into HTML using a template,
3. and map URLs to data.

Using [YAMLtree][] as the datastore, Oak commits you to a hierarchical data structure. This gives you URL mapping straight away: `papers.published.paper1` becomes `/papers/published/paper1.html`. 

Oak comes with default templates for listings so that `/papers/published/index.html` works out of the box as you expect it.

Template inheritance also follows the tree structure.


[YAMLTree]: https://github.com/korenmiklos/yamltree
[Jinja2]: http://jinja.pocoo.org/docs/


