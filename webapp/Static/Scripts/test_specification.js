


const divider = document.getElementById('divider');
const leftPane = document.querySelector('.left-pane');

let isResizing = false;


divider.addEventListener('mousedown', (e) => {
    isResizing = true;
    document.body.style.cursor = 'col-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    const newWidth = e.clientX;
    if (newWidth > 150 && newWidth < 600) {
        leftPane.style.width = newWidth + 'px';
    }
});

document.addEventListener('mouseup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});

$('#testTree').jstree({
    'core': {
        'data': {
            'url': function (node) {
                // If root node, request toplevel items
                return node.id === '#' ? '/get_test_tree_root' : '/get_test_tree_children';
            },
            'data': function (node) {
                return { 'id': node.id };
            }
        },
        "check_callback": true
    },
    "types": {
        "suite": {
            "icon": "custom-suite-icon"
        },
        "test": {
            "icon": "custom-test-icon"
        }
    },
    "state": { "key": "state_demo" },

    contextmenu: {
        items: function (node) {
            return getContextMenuItems(node);
        }
    },

    "plugins": ["state", "wholerow", "unique", "dnd", "types", "contextmenu"]
});

let clipboard = {
    node: null,
    action: null // 'copy' or 'cut'
};

function handleCopy(tree, node, action) {
    clipboard.data = tree.get_json(node, { flat: true }); // Full nested structure
    clipboard.action = action;
}


function handleRename(tree, node) {
    if (node.parent == "#") {
        alert("It is not possible to rename the root suite!");
        return;
    }

    tree.edit(node, null, function (new_node) {
        is_new_node_name_unique = validate_new_node_name(new_node.text, node.parent, tree)
        if (new_node.text && new_node.text.trim() !== '' && is_new_node_name_unique) {
            fetch('/rename_node', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    id: node.id,
                    new_name: new_node.text.trim(),
                    type: node.type
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert("Rename failed: " + data.error);
                    } else {
                        tree.refresh_node(node.parent_id)
                    }
                })
                .catch(err => {
                    console.error('Rename error:', err);
                    alert("Error contacting server.");
                });
        }
    });
}


function handleDelete(tree, node) {
    if (node.parent == "#") {
        alert("It is not possible to delete a root suite!");
        return;
    }
    if (!confirm("Are you sure you want to delete this item?")) return;

    fetch('/delete_node', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            id: node.id,
            type: node.type
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                tree.delete_node(node);
            } else {
                alert("Delete failed: " + data.error);
            }
        })
        .catch(err => {
            console.error('Delete error:', err);
            alert("Error contacting server.");
        });
}

function handleAddNode(tree, parentNode, Filetype) {


    //Prevent adding suite to a test case
    if (parentNode.type === "test") {
        return;
    }

    let route = "/add_suite"
    // Create temporary node
    const tempId = tree.create_node(parentNode, {
        text: Filetype == "suite" ? "New suite" : "New testcase",
        type: Filetype
    });

    if (!tempId) {
        alert("Failed to create temporary node.");
        return;
    }

    const tempNode = tree.get_node(tempId);


    if (Filetype == "suite") {
        route = "/add_suite"
    } else {
        route = "/add_test_case"
    }

    tree.edit(tempNode, null, function (newName) {
        // Handle cancel or empty input
        if (!newName.text || newName.text.trim() === "") {
            tree.delete_node(tempNode);  // Clean up if name invalid
            return;
        }

        //Send to backend
        fetch(route, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({
                parent_id: parentNode.id,
                name: newName.text.trim()
            })
        })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert("Backend rejected the creation: " + data.error);
                    tree.delete_node(tempNode);  // rollback
                } else {
                    tree.refresh_node(parentNode)
                }
            })
            .catch(error => {
                console.error("Error contacting backend:", error);
                alert("Error contacting the server.");
                tree.delete_node(tempNode);  // cleanup on error
            });
    });



}



function handlePaste(tree, targetNode) {
    if (!clipboard.data) return;

    copied_nodes = clipboard.data;

    success = false;

    if (copied_nodes.type == "test") {

        success = handlecopytest(tree, targetNode, copied_nodes[0].id)
        return;
    }

    // else: suite
    success = handlecopysuite(tree, targetNode, copied_nodes[0])

    if (clipboard.action == "cut" && success) {
        handleDelete(tree, copied_nodes)
    }

    //  Clear clipboard
    clipboard.node = null;
    clipboard.data = null;
    clipboard.action = null;
}


function getContextMenuItems(node) {
    const tree = $('#testTree').jstree(true);
    const isTestNode = node.type === 'test';
    const isRoot = node.parent === '#';


    return {
        addTestCase: {
            label: "Add Test Case",
            _disabled: isTestNode,
            action: () => handleAddNode(tree, node, 'test')
        },
        addTestSuite: {
            label: "Add Test Suite",
            _disabled: isTestNode,
            action: () => handleAddNode(tree, node, 'suite')
        },
        renameItem: {
            label: "Rename",
            _disabled: isRoot,
            action: () => handleRename(tree, node)
        },

        copy: {
            label: "Copy",
            _disabled: isRoot,
            action: () => handleCopy(tree, node, action = "copy")
        },
        cut: {
            label: "Cut",
            _disabled: isRoot,
            action: () => handleCopy(tree, node, action = "cut")
        },
        paste: {
            label: "Paste",
            _disabled: isTestNode || !clipboard.data,  // Disable if clipboard is empty
            action: () => handlePaste(tree, node)
        },
        deleteItem: {
            label: "Delete",
            _disabled: isRoot,
            action: () => handleDelete(tree, node)
        }
    };
}

function validate_new_node_name(node_name, parent_id, tree) {
    const parentNode = tree.get_node(parent_id);

    parentNode.children.forEach((child) => {
        if (tree.get_node(child).text == node_name) return false;
    });


    return true;
}

function handlecopytest(tree, parentNode, test2copyID) {
    fetch('/paste_test_case', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            parent_id: parentNode.id,
            test_id: test2copyID
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {

                tree.refresh_node(parentNode)
                return true;

            } else {
                alert("Copy failed: " + data.error);
                return false;
            }
        })
        .catch(err => {
            console.error('Copy error:', err);
            alert("Error contacting server.");
        });
}


function handlecopysuite(tree, parentNode, suiteNode) {
    openAllLazyNodes(tree, suiteNode.id, function () {
        // After all children are loaded and opened
        const allNodes = tree.get_json(suiteNode, { flat: true });  // Gets suite + descendants as flat array

        // Optional: Sort so that parents come before their children
        allNodes.sort((a, b) => a.parent.localeCompare(b.parent));

        const childIds = allNodes
            .filter(n => n.id !== suiteNode.id) // return only the childs id
            .map(n => ({ id: n.id, parent: n.parent }));

        fetch('/paste_suite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                parent_id: parentNode.id,
                suite_id: suiteNode.id,
                children: childIds
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    tree.close_all(suiteNode)
                    tree.refresh_node(parentNode);

                } else {
                    alert("Copy failed: " + data.error);
                }
            })
            .catch(err => {
                console.error('Copy error:', err);
                alert("Error contacting server.");
            });
    });
}


function openAllLazyNodes(tree, nodeId, onComplete) {
    tree.open_node(nodeId, function (openedNode) {
        const children = openedNode.children;

        if (!children || children.length === 0) {
            return onComplete(); // No children to process
        }

        let remaining = children.length;

        children.forEach(childId => {
            openAllLazyNodes(tree, childId, function () {
                remaining--;
                if (remaining === 0) {
                    onComplete(); // All children processed
                }
            });
        });
    }, true); // true forces loading if necessary
}