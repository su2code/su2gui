from collections import defaultdict
import copy

class PipelineManager:
    """ Create gittree type trees
        usage:

        create a new pipeline:
        pipeline = PipelineManager(state, "git_tree")

        add a node:
        id_root = pipeline.add_node(name="Mesh", subui="none", visible=0, color="#9C27B0", actions=["collapsible"])
        id_a = pipeline.add_node(parent=id_root, name="a", subui="none", visible=1, color="#42A5F5")

        string name: name of the node
        string subui = connect a user interface to this node
        bool visible = node is visible or not
        HEX color = color of the node
        actions = collapsible: this node is collapsible
    """
    DEFAULT_NODE = {"name": "undefined", "visible": 0, "collapsed": 0}

    def __init__(self, state, name):
        """ initialize the pipeline """
        self._state = state
        self._name = name
        self._next_id = 1
        self._nodes = {}
        self._children_map = defaultdict(set)

    def _update_hierarchy(self):
        """ update the pipeline hierarchy """
        self._children_map.clear()
        for node in self._nodes.values():
            self._children_map[node.get("parent")].add(node.get("id"))

        self.update()

    def _add_children(self, list_to_fill, node_id):
        """ add children to the hierarchy"""

        # if the node is not the root node, add it to the list
        if (node_id != '0'):
          node = self._nodes[node_id]
          list_to_fill.append(node)

        # then inspect the children of the node
        childrenset = list(map(int, self._children_map[node_id]))
        # 1 child
        if (len(childrenset)==1) :
          nodeChild = self._nodes[str(childrenset[0])]
          self._add_children(list_to_fill, nodeChild.get("id"))

        else:
          # we have 2 (or more) children
          for child_id in self._children_map[node_id]:
            nodeChild = self._nodes[child_id]
            # if the current node is collapsed, we take the largest ID branch
            if node.get("collapsed"):
              nodeNonCollapsed = max(childrenset)
              if (child_id == str(nodeNonCollapsed)):
                self._add_children(list_to_fill, nodeChild.get("id"))
            else:
                self._add_children(list_to_fill, nodeChild.get("id"))

        return list_to_fill

    def update(self):
        """ Update the children and the state """
        result = self._add_children([], "0")
        self._state[self._name] = result
        return result

    def add_node(self, parent="0", name="none",headnode="0",left=True, **item_keys):
        """ Add a node to the pipeline
            Optional: left={True,False}: if left is true, then try to place the node in the left branch
            if left is false, try to place the node in the right branch, provided a left branch already exists
            Note that the left branch is the default, main branch.
          """

        #print("item_keys=",item_keys)

        _id = f"{self._next_id}"
        self._next_id += 1

        # if the node itself is a headnode
        if headnode=="0":
          headnode=name

        node = {
            **PipelineManager.DEFAULT_NODE,
            "id": _id,
            "parent": parent,
            "name": name,
            # if the node is itself a headnode, the value is 0, else the value is the name of the head node
            "headnode": headnode,
            **item_keys,
        }

        self._nodes[_id] = node

        self._update_hierarchy()

        return _id

    # append a node at the end to the branch called parent
    def append_node(self, parent_name, left=True, **item_keys):
        """ Add a node to the pipeline
            Optional: left={True,False}: if left is true, then try to place the node in the left branch
            if left is false, try to place the node in the right branch, provided a left branch already exists
            Note that the left branch is the default, main branch.
          """

        #print(self._nodes)
        #for k in self._nodes:
        #  print(k, ", node =  ", self._nodes[k])

        # get the id of the node with name 'parent_name'
        for k in self._nodes:
            if self._nodes[k]['name']== parent_name:
              parent_id = k

        # create a new id
        _id = f"{self._next_id}"
        self._next_id += 1

        node = {
            **PipelineManager.DEFAULT_NODE,
            "id": _id,
            "parent": parent_id,
            "headnode": parent_name,
            **item_keys,
        }
        #print("append node: ",node)
        # at this point we check where we need to insert the node. If a node already exists,
        # and left=True, then simply add the node. If left=False, we need to swap it with the
        # existing node and make it the lowest node of all nodes in the branch
        # first, find all nodes that have the same parent.
        parentlist = self.get_parents(parent_id)
        parentlist.sort(key=int)
        #print("all nodes with the same parent = ",parentlist)

        # check if we need to place it to the right

        # right list exists:we add it and we point to the parent
        if (len(parentlist)==2 and (left==False)):
           #print("adding to existing right-list")
           self._nodes[_id] = node
           # first in the sorted list is the right-list
           descendantsList=[parentlist[0]]
           self.get_descendants(parentlist[0],descendantsList)
           #print("descendants = ",descendantsList)
           self._nodes[_id]['parent'] = descendantsList[-1]

        elif (len(parentlist)==1 and (left==False)):
          #print("creating new right-list")

          parentlist.append(_id)
          # all nodes with the same parent
          for i in range(len(parentlist)-1):
            parent = parentlist[i]
            name = self._nodes[parent]['name']
            children = self.get_children(name)
            #print("child = ",children)
            for child in children:
              # move the parents
              self._nodes[child]['parent'] = parentlist[i+1]


          for i in range(len(parentlist)-1):
            self._nodes[parentlist[i+1]] = copy.deepcopy(self._nodes[parentlist[i]])
            self._nodes[parentlist[i+1]]['id'] = parentlist[i+1]

          self._nodes[parentlist[0]] = node
          self._nodes[parentlist[0]]['id'] = parentlist[0]

        #  parentlist.append(_id)
        #  print("parentlist=",parentlist)
        #  # move all nodes up to a different key
        #  for i in range(len(parentlist)-1):
        #    # move all nodes in parentlist up to a different key
        #    self._nodes[parentlist[i+1]] = self._nodes[parentlist[i]]
        #    # point the children of all nodes to the right key
        #    childrenlist = self.get_children(parentlist[i])
        #    for k in childrenlist:
        #       self._nodes[k]['parent'] = parentlist[i+1]
        #
        #  self._nodes[0] = node
        #else:
        #  self._nodes[_id] = node

        #print("**********************************")
        #print("finished! add:",self._nodes)
        #for k in self._nodes:
        #  print(self._nodes[k])
        #print("**********************************")
        self._update_hierarchy()

        return _id

    def toggle_collapsed(self, _id, icons=["collapsed", "collapsible"]):
        """ toggle if the node is shown as collapsed or not. Collapsed means we do not show its right children """
        # what we want is to only toggle the collapse for the 'right' path and not the 'left' path.
        #print("toggle collapsed for id ",_id)
        node = self.get_node(_id)
        node["collapsed"] = not node["collapsed"]

        # Toggle matching action icon
        actions = node.get("actions", [])
        for i in range(len(actions)):
            action = actions[i]
            if action in icons:
                actions[i] = icons[(icons.index(action) + 1) % 2]

        self.update()

        return node["collapsed"]

    def get_node(self, _id):
        """ get the node from the dictionary based on the key """
        return self._nodes.get(f"{_id}")

    # remove a node and update the children
    # input: string _id
    def remove_node(self,_id):
        """ remove a node based on the key of the node, and move all children up """
        #print("list=",self._nodes)

        # step 1: get the parent of the node
        root_node = self.get_node(_id)
        #print("root node=",root_node)

        if (root_node == None):
            #print("root node is none")
            return

        parent_id = root_node['parent']
        #print("parent id=",parent_id)

        if (parent_id == None):
            return

        # find the node that has _id as a parent (assume it is only one)
        child_found = False
        for k in self._nodes:
            #print("k=",k)
            if self._nodes[k]['parent']==_id:
              child_found = True
              #print("parent is ",_id)
              # copy the entire child entry to the current
              self._nodes[_id] = copy.deepcopy(self._nodes[k])
              # copy the parent id of the child to the current
              self._nodes[_id]['parent']=parent_id
              self._nodes[_id]['id'] = _id
              #print("self nodes = ",self._nodes)
              self.remove_node(k)
              break

        # only delete the final entry that has no child
        if (child_found == False):
          # if we did not find another child, delete this node
          del self._nodes[_id]
          self._update_hierarchy()
          #self.update()

    # remove a node and update the children
    # input: string _id
    def remove_node_and_children(self,_id):
        """ Remove a node and all right children. We keep the left children. """
        # step 1: get the root node
        if (self.get_node(_id) == None):
            #print("root node is none")
            return

        # get all descendants of _id
        l = []
        self.get_descendants(_id,l)
        #print("list = ",l)
        del self._nodes[_id]
        for k in l:
           del self._nodes[k]

        self._update_hierarchy()
        #self.update()


    # remove the right subnode from the main node with name "_name"
    # note that we have to remove the "right" subnodes and not the "left" subnodes
    # The "right" subnodes are the subnodes where the first subnode has the lowest id
    def remove_right_subnode(self, _name):
        """ Remove the node and all right children. """

        # first, find the id of the node with name "_name"
        root_id = -1

        for k in self._nodes:
          #print(self._nodes[k])
          if self._nodes[k]['name']==_name:
              root_id = int(self._nodes[k]['id'])
              #print("root id found:",root_id)

        #if (root_id>0):
        #  print("root id found, now find the left and right nodes")

        child_node_id = []
        for k in self._nodes:
          current_id = int(self._nodes[k]['id'])
          parent_id = int(self._nodes[k]['parent'])
          # note that the right id is the smallest and the left id is the largest
          if (parent_id == root_id):
            child_node_id.append(current_id)
        child_node_id.sort()

        #print("child_node_id=",child_node_id)

        if len(child_node_id) == 2:
          right_node = child_node_id[0]
          #print("right node found at:",right_node)
          self.remove_node_and_children(str(right_node))
          #self.update()

        #print(self._nodes)
        #for k in self._nodes:
        #  print(self._nodes[k])

        #elif len(child_node_id) > 2:
        #    print("more than 2 child nodes found!")
        #else:
        #    print("less than 2 children found, doing nothing")

    # change the value of _key of the node with name "name"
    def update_node_value(self, _name,_key,_value):
        """ For a node with 'name'=_name, apply _key = _value """
        for k in self._nodes:
            #print("node=",k)
            if self._nodes[k]['name']==_name:
              #print("node ",k," has name ",_name, ", changing value of ",_key ," to ",_value)
              self._nodes[k][_key] = _value

    def get_parents(self, _parent):
        """ For _parent, return a list of all nodes with the same parents """
        parent_list=[]
        #print("find nodes with parent ",_parent)
        for k in self._nodes:
            #print("node=",self._nodes[k])
            if self._nodes[k]['parent']==_parent:
              parent_list.append(k)
        return parent_list

    def get_id(self,_name):
        """ for _name, get the id (key) in the dictionary """
        index = None
        for k in self._nodes:
          if self._nodes[k]['name']==_name:
            index = k
        return index

    def get_children(self, _name):
        """ For _name, return a sorted list of all nodes that are children of name """
        children_list=[]
        #print("find children of ",_name)
        index = self.get_id(_name)
        for k in self._nodes:
            #print("node=",self._nodes[k])
            if self._nodes[k]['parent']==index:
              children_list.append(k)
        children_list.sort()
        return children_list

    def get_descendants(self, _id, descendants_list=[]):
        """ For _id, return a sorted list of all nodes that are descendants of name """
        #print("find descendants of ",_id)
        #index = self.get_id(_name)
        #print("descendants_list = ",descendants_list)
        for k in self._nodes:
            #print("get_descendants::node=",self._nodes[k])
            if self._nodes[k]['parent']==_id:
              #child_name = self._nodes[k]['name']
              descendants_list.append(k)
              child = self.get_descendants(k,descendants_list)

        #print("descendants=",descendants_list)
        #return descendants_list