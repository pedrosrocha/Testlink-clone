// Contains all the logic for the jstree test specification tree

$('#testTree').jstree({
    'core': {
        'data': {
            'url': function (node) {
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
    "contextmenu": {
        "items": function (node) {
            if (user_level == 'viewer') return;

            return getContextMenuItems(node);
        }
    },
    "plugins": ["state", "wholerow", "unique", "dnd", "types", "contextmenu"]
});

function handleCopy(tree, node, action) {
    clipboard.data = tree.get_json(node, { flat: true });
    clipboard.action = action;
}

function handleRename(tree, node) {
    if (node.parent == "#") {
        alert("It is not possible to rename the root suite!");
        return;
    }
    tree.edit(node, null, function (new_node) {
        let is_new_node_name_unique = validate_new_node_name(new_node, node.parent, tree);
        if (new_node.text && new_node.text.trim() !== '' && is_new_node_name_unique) {
            fetch('/rename_node', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ id: node.id, new_name: new_node.text.trim(), type: node.type })
            })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert("Rename failed: " + data.error);
                    } else {
                        tree.refresh_node(node.parent);
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
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ id: node.id, type: node.type })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                tree.delete_node(node);
                ShowSuite(node.parent)
            } else {
                alert("Delete failed: " + data.error);
            }
        })
        .catch(err => {
            console.error('Delete error:', err);
            alert("Error contacting server.");
        });
}

function handleAddNode(tree, parentNode, fileType) {
    if (parentNode.type === "test") {
        return;
    }

    const route = fileType === "suite" ? "/add_suite" : "/add_test_case";
    tree.open_node(parentNode, () => { //opens the node to garantee thta the temp file will created successfully

        const tempId = tree.create_node(parentNode, {
            text: fileType === "suite" ? "New suite" : "New testcase",
            type: fileType
        });
        if (!tempId) {
            alert("Failed to create temporary node.");
            return;
        }

        const tempNode = tree.get_node(tempId);
        tree.edit(tempNode, null, function (newName) {
            if (!newName.text || newName.text.trim() === "") {
                tree.delete_node(tempNode);
                return;
            }
            fetch(route, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
                body: JSON.stringify({ parent_id: parentNode.id, name: newName.text.trim() })
            })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert("Backend rejected the creation: " + data.error);
                        tree.delete_node(tempNode);
                    } else {
                        tree.refresh_node(parentNode);
                    }
                })
                .catch(error => {
                    console.error("Error contacting backend:", error);
                    alert("Error contacting the server.");
                    tree.delete_node(tempNode);
                });
        });
    });


}

function handlePaste(tree, targetNode) {
    if (!clipboard.data) return;
    const copied_nodes = clipboard.data;

    if (copied_nodes[0].type == "test" && clipboard.action == "copy") {
        handlecopytest(tree, targetNode, copied_nodes[0].id);
    } else if (copied_nodes[0].type == "suite" && clipboard.action == "copy") {
        handlecopysuite(tree, targetNode, copied_nodes[0]);
    } else { // cut action
        HandleMove(copied_nodes[0].id, targetNode.id, copied_nodes[0].type);
        tree.refresh();
    }

    // Clear clipboard after paste
    clipboard.node = null;
    clipboard.data = null;
    clipboard.action = null;
}

function getContextMenuItems(node) {
    if (user_level == 'viewer') return;
    const tree = $('#testTree').jstree(true);
    const isTestNode = node.type === 'test';
    const isRoot = node.parent === '#';
    return {
        addTestCase: {
            label: " Add Test Case",
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
            action: () => handleCopy(tree, node, "copy")
        },
        cut: {
            label: "Cut",
            _disabled: isRoot,
            action: () => handleCopy(tree, node, "cut")
        },
        paste: {
            label: "Paste",
            _disabled: isTestNode || !clipboard.data,
            action: () => handlePaste(tree, node)
        },
        deleteItem: {
            label: "Delete",
            _disabled: isRoot, action: () => handleDelete(tree, node)
        }
    };
}

function validate_new_node_name(node, parent_id, tree) {
    const parentNode = tree.get_node(parent_id);
    for (const childId of parentNode.children) {
        child = tree.get_node(childId)
        if (child.text === node.text && child.id != node.id) {
            return false;
        }
    }
    return true;
}

function handlecopytest(tree, parentNode, test2copyID) {
    fetch('/paste_test_case', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ parent_id: parentNode.id, test_id: test2copyID })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                tree.refresh_node(parentNode);
            } else {
                alert("Copy failed: " + data.error);
            }
        })
        .catch(err => {
            console.error('Copy error:', err);
            alert("Error contacting server.");
        });
}

function handlecopysuite(tree, parentNode, suiteNode) {
    return new Promise((resolve, reject) => {
        openAllLazyNodes(tree, suiteNode.id, function () {
            const allNodes = tree.get_json(suiteNode, { flat: true });
            allNodes.sort((a, b) => a.parent.localeCompare(b.parent));
            const childIds = allNodes.filter(n => n.id !== suiteNode.id).map(n => ({ id: n.id, parent: n.parent }));
            fetch('/paste_suite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ parent_id: parentNode.id, suite_id: suiteNode.id, children: childIds })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        tree.close_all(suiteNode);
                        tree.refresh_node(parentNode);
                        resolve(true);
                    } else {
                        alert("Copy failed: " + data.error);
                        resolve(false);
                    }
                })
                .catch(err => {
                    console.error('Copy error:', err);
                    alert("Error contacting server.");
                    resolve(false);
                });
        });
    });
}

function openAllLazyNodes(tree, nodeId, onComplete) {
    tree.open_node(nodeId, function (openedNode) {
        const children = openedNode.children;
        if (!children || children.length === 0) {
            return onComplete();
        }
        let remaining = children.length;
        children.forEach(childId => {
            openAllLazyNodes(tree, childId, function () {
                remaining--;
                if (remaining === 0) {
                    onComplete();
                }
            });
        });
    }, true);
}

function HandleMove(node_id, node_new_parent, node_type) {
    fetch(node_type === 'suite' ? '/move_suite' : '/move_test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ node_id: node_id, parent_id: node_new_parent })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Move failed: " + data.error);
                const tree = $('#testTree').jstree(true);
                tree.refresh();
            }
        })
        .catch(err => {
            console.error('Move error:', err);
            alert("Error contacting server.");
        });
}

$('#testTree').on('move_node.jstree', function (e, data) {
    HandleMove(data.node.id, data.node.parent, data.node.type);
});

document.addEventListener('keydown', function (e) {
    const tree = $('#testTree').jstree(true);
    const selectedNodeId = tree.get_selected()[0];
    if (!selectedNodeId) return;

    const selectedNode = tree.get_node(selectedNodeId);
    if (!document.querySelector('#testTree').contains(document.activeElement) || ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    if (e.key === "F2") { e.preventDefault(); handleRename(tree, selectedNode); }
    if (e.key === "Delete") { e.preventDefault(); handleDelete(tree, selectedNode); }
    if (e.key.toLowerCase() === "c" && e.ctrlKey) { e.preventDefault(); handleCopy(tree, selectedNode, "copy"); }
    if (e.key.toLowerCase() === "x" && e.ctrlKey) { e.preventDefault(); handleCopy(tree, selectedNode, "cut"); }
    if (e.key.toLowerCase() === "v" && e.ctrlKey) { e.preventDefault(); handlePaste(tree, selectedNode); }
});

$('#testTree').on("select_node.jstree", function (e, data) {
    const pane = document.getElementById("details-pane");

    if (data.node.type === "test") {
        const testId = data.node.id.replace("c_", "");
        currentTestSuiteId = null;
        currentTestCaseId = testId;

        pane.dataset.suiteId = "";
        pane.dataset.testId = testId;

        ShowTestCase(testId);
    } else {
        const suiteId = data.node.id;
        currentTestSuiteId = suiteId;
        currentTestCaseId = null;

        pane.dataset.suiteId = suiteId;
        pane.dataset.testId = "";

        ShowSuite(suiteId);
    }
});