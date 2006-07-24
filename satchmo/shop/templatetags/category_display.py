from django.template import Library, Node
from satchmo.product.models import Category

register = Library()

def category_tree(category_root):
    """
    Creates an unnumbered list of the categories.  For example:
    <ul>
        <li>Books</li>
            <ul>
            <li>Science Fiction</li>
                <ul>
                <li>Space stories</li>
                <li>Robot stories</li>
                </ul>
            <li>Non-fiction</li>
            </ul>
    </ul>
    """
    category = Category.objects.get(id=category_root)
    output = "<ul>\n"
    temp_list, depth_list = category._recurse_for_children(category,0)
    temp_list.insert(0,category)
    depth_list.insert(0,0)
    child_list = zip(temp_list,depth_list)
    prior_depth = 0
    for item in child_list:
        tabs = "\t" * item[1]    
        if item[1] == prior_depth:
            output += tabs + '<li><a href="%s">%s</a></li>\n' % (item[0].get_absolute_url(), item[0].name)

        if item[1] > prior_depth:
            output += tabs + "<ul>\n"
            output += tabs + '<li><a href="%s">%s</a></li>\n' % (item[0].get_absolute_url(), item[0].name)
                
        if item[1] < prior_depth:
            diff = prior_depth - item[1]
            for count in range(0,diff):
                output += tabs + "</ul>\n"
            output += tabs + '<li><a href="%s">%s</a></li>\n' % (item[0].get_absolute_url(), item[0].name) 
            
        prior_depth = item[1]
        tabs = "\t"    
    output +="</ul>\n</ul>\n"
    return output

register.simple_tag(category_tree)