from django.template import Library, Node
from satchmo.product.models import Category
from elementtree.ElementTree import Element, SubElement, tostring

register = Library()

def recurse_for_children(current_node, parent_node):
    if current_node.child.count() > 0:
        temp_parent = SubElement(parent_node,"li")
        attrs = { 'href' : current_node.get_absolute_url() }
        link = SubElement(temp_parent, "a", attrs)
        link.text = current_node.name
        new_parent = SubElement(temp_parent,"ul")
        children = current_node.child.all()
        for child in children:
            recurse_for_children(child, new_parent)
    else:
        temp_parent = SubElement(parent_node,"li")
        attrs = { 'href' : current_node.get_absolute_url() }
        link = SubElement(temp_parent, "a", attrs)
        link.text = current_node.name


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
    return tostring(root)

register.simple_tag(category_tree)