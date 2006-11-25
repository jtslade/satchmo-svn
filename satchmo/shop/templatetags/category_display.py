from django.template import Library, Node
from satchmo.product.models import Category

try:
    from xml.etree.ElementTree import Element, SubElement, tostring
except ImportError:
    from elementtree.ElementTree import Element, SubElement, tostring 

register = Library()

def recurse_for_children(current_node, parent_node, show_empty=True):
    if current_node.child.count() > 0:
        temp_parent = SubElement(parent_node,"li")
        attrs = { 'href' : current_node.get_absolute_url() }
        link = SubElement(temp_parent, "a", attrs)
        link.text = unicode(current_node.name,'utf-8')
        new_parent = SubElement(temp_parent,"ul")
        children = current_node.child.all()
        for child in children:
            recurse_for_children(child, new_parent)
    elif current_node.item_set.count() > 0:
        temp_parent = SubElement(parent_node,"li")
        attrs = { 'href' : current_node.get_absolute_url() }
        link = SubElement(temp_parent, "a", attrs)
        link.text = unicode(current_node.name,'utf-8') 
    elif current_node.item_set.count() == 0 and show_empty:
        temp_parent = SubElement(parent_node,"li")
        attrs = { 'href' : current_node.get_absolute_url() }
        link = SubElement(temp_parent, "a", attrs)
        link.text = unicode(current_node.name,'utf-8')

def category_tree():
    """
    Creates an unnumbered list of the categories.  For example:
    <ul>
        <li>Books
            <ul>
            <li>Science Fiction
                <ul>
                <li>Space stories</li>
                <li>Robot stories</li>
                </ul>
            </li>
            <li>Non-fiction</li>
            </ul>
    </ul>
    """
    root = Element("ul")
    for cats in Category.objects.all():
        if not cats.parent:
            recurse_for_children(cats, root)
    return tostring(root, 'utf-8')

register.simple_tag(category_tree)