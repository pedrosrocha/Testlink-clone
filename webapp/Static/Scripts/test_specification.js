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
                // If root node, request top-level items
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

function handleCopy(tree, node) {
    clipboard.data = tree.get_json(node, { flat: true }); // Full nested structure
    clipboard.action = 'copy';
}


function handleRename(tree, node) {
    if (node.parent == "#") {
        alert("It is not possible to rename the root suite!");
        return;
    }

    tree.edit(node, null, function (new_node) {

        if (new_node.text && new_node.text.trim() !== '') {
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

function handleAddNode(tree, parentNode, type) {
    const newNode = tree.create_node(parentNode, {
        text: type === 'suite' ? 'New suite' : 'New testcase',
        type: type
    });

    if (parentNode.type == "test") {
        return;
    }
    if (newNode.type == "suite") {
        tree.edit(newNode, null, function (new_name) {
            if (new_name.text && new_name.text.trim() !== '') {
                fetch('/add_suite', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        parent_id: parentNode.id,
                        name: new_name.text.trim(),
                    })
                });
            }
        });
        return;
    }
    tree.edit(newNode, null, function (new_name) {
        if (new_name.text && new_name.text.trim() !== '') {
            fetch('/add_test_case', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    parent_id: parentNode.id,
                    name: new_name.text.trim(),
                    type: type
                })
            });
        }
    });
    return;

}


function handlePaste(tree, targetNode) {
    if (!clipboard.data) return;

    function pasteRecursive(targetId, flatData) {
        // Mapping from old ID to new ID
        const idMap = {};

        // Find the root node (the one that was copied or cut)
        const root = flatData.find(n => n.parent === '#');
        if (!root) return;

        // Create root under target
        const newRootId = $('#testTree').jstree().create_node(targetId, {
            text: root.text + ' (copy)',
            type: root.type
        });

        idMap[root.id] = newRootId;

        // Process all other nodes
        function createChildrenRecursive(parentOldId, parentNewId) {
            flatData.forEach(node => {
                if (node.parent === parentOldId) {
                    const newId = $('#testTree').jstree().create_node(parentNewId, {
                        text: node.text,
                        type: node.type
                    });

                    idMap[node.id] = newId;

                    // Recursively process this node’s children
                    createChildrenRecursive(node.id, newId);
                }
            });
        }

        createChildrenRecursive(root.id, newRootId);
    }



    //  Start recursive paste
    pasteRecursive(targetNode.id, clipboard.data);


    //  If cut, delete original node after pasting
    if (clipboard.action === 'cut') {
        tree.delete_node(clipboard.node);
    }

    var id_list = [];

    clipboard.data.forEach(function (cur_node) {
        id_list.push({
            "id": cur_node.id,
            "type": cur_node.type
        })

    });


    //  Send to backend for persistence
    fetch('/paste_node', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            target_id: targetNode.id,
            list_suites_tests: id_list
        })
    });

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
            action: () => handleCopy(tree, node)
        },
        cut: {
            label: "Cut",
            _disabled: isRoot,
            action: () => handleCopy(tree, node)
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
