
const divider = document.getElementById('divider');


let currentSuiteId = null;
let currentTestCaseId = null;
let StepAlreadyClicked = false;
let EditingSteps = false;
var sortablehandler;

let isResizing = false;
let debounceTimer;
let clipboard = {
    node: null,
    action: null // 'copy' or 'cut'
};
let new_steps_order_payload = null;
let stepid_clipboard = null;
let user_level = null;

document.addEventListener('DOMContentLoaded', function () {
    //function that handles the user level initialization

    fetch('/get_user_level', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        //body: JSON.stringify({})
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Not possible read the current user level: " + data.message);
            } else {
                user_level = data.user_level;
            }
        })
        .catch(err => {
            console.error('Not possible to read the current user level:', err);
        });

    if (user_level == 'viewer') {
        sortablehandler.option("disabled", true);
    }

});


divider.addEventListener('mousedown', (e) => {
    isResizing = true;
    document.body.style.cursor = 'col-resize';
});

document.addEventListener('mousemove', (e) => {
    const leftColumn = document.getElementById('left-column');

    if (!isResizing) return;

    const newWidth = e.clientX;

    leftColumn.style.width = newWidth + 'px';
});

document.addEventListener('mouseup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});

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


document.getElementById("details-pane").addEventListener("submit", function (event) {

    let clickedid = document.getElementById("details-pane").dataset.testId;
    if (document.getElementById("details-pane").dataset.suiteId) {
        clickedid = document.getElementById("details-pane").dataset.suiteId;
    }


    if (event.target && event.target.id === 'edit-test-case-form') {
        HandleEditTestCase(event, "c_" + clickedid)
    } else if (event.target && event.target.id === 'edit-suite-form') {
        HandleEditSuite(event, clickedid)
    } else if (event.target && event.target.id === 'add-suite-form') {
        HandleAddSuite(event, clickedid)
    } else if (event.target && event.target.id === 'add-test-case-form') {
        HandleAddTest(event, clickedid)
    }
});

function HandleEditTestCase(event, id) {
    event.preventDefault(); // Prevent default form submission

    const form = event.target;
    const formData = new FormData(form);
    const testcaseId = id

    const new_test_data = {
        id: testcaseId,
        name: formData.get('name'),
        description: formData.get('description'),
        preconditions: formData.get('preconditions'),
        expected_results: formData.get('expected_result'),
        priority: formData.get('priority'),
        status: formData.get('status')
    };

    fetch('/update_test_case', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(new_test_data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                ShowTestCase(testcaseId); // Reload the test case view
                const tree = $('#testTree').jstree(true);
                const testcaseNode = tree.get_node(testcaseId);
                const ParentNode = tree.get_node(testcaseNode.parent);
                tree.refresh_node(ParentNode);
            } else {
                alert('Error updating test case: ' + data.error);
            }
        })
        .catch(err => {
            console.error('Error updating test case:', err);
            alert('An error occurred while updating the test case.');
        });
}

function HandleEditSuite(event, id) {
    event.preventDefault(); // Prevent default form submission

    const form = event.target;
    const formData = new FormData(form);
    const suiteID = id;

    const new_suite_data = {
        id: suiteID,
        name: formData.get('name'),
        description: formData.get('description'),
    };

    fetch('/update_suite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(new_suite_data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                ShowSuite(suiteID); // Reload the test case view

                const tree = $('#testTree').jstree(true);
                const suiteNode = tree.get_node(suiteID);
                const ParentNode = tree.get_node(suiteNode.parent);
                tree.refresh_node(ParentNode);
            } else {
                alert('Error updating suite: ' + data.error);
            }
        })
        .catch(err => {
            console.error('Error updating suite:', err);
            alert('An error occurred while updating the suite.');
        });
}

function HandleAddSuite(event, parentId) {
    event.preventDefault(); // Prevent default form submission

    const form = event.target;
    const formData = new FormData(form);


    const tree = $('#testTree').jstree(true);
    const parentNode = tree.get_node(parentId)

    const new_suite_data = {
        parent_id: parentNode.id,
        name: formData.get('name'),
        description: formData.get('description')
    }



    if (parentNode.type === "test") {
        return;
    }


    fetch("/add_suite", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify(new_suite_data)
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Backend rejected the creation: " + data.error);
            } else {
                tree.refresh_node(parentNode);
            }
        })
        .catch(error => {
            console.error("Error contacting backend:", error);
            alert("Error contacting the server.");
        });

}

function HandleAddTest(event, parentId) {
    event.preventDefault(); // Prevent default form submission

    const form = event.target;
    const formData = new FormData(form);

    const tree = $('#testTree').jstree(true);
    const parentNode = tree.get_node(parentId)

    const new_test_data = {
        name: formData.get('name'),
        parent_id: parentNode.id,
        description: formData.get('description'),
        expected_results: formData.get('expected_results'),
        precondition: formData.get('preconditions'),
        status: formData.get('status'),
        priority: formData.get('priority')
    }



    if (parentNode.type === "test") {
        return;
    }

    fetch("/add_test_case", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify(new_test_data)
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Backend rejected the creation: " + data.error);
            } else {
                tree.refresh_node(parentNode);
            }
        })
        .catch(error => {
            console.error("Error contacting backend:", error);
            alert("Error contacting the server.");
        });

}


function ShowTestCase(testcaseId) {

    if (testcaseId.startsWith("c")) testcaseId = testcaseId.replace("c_", "");

    fetch(`/get_testcase_html/${testcaseId}`)
        .then(response => response.text())
        .then(html => {
            document.getElementById("details-pane").innerHTML = html;


            CreateSortable(testcaseId);


            const SpanEditModeValue = document.querySelector('#editing-steps-value');

            if (!SpanEditModeValue) return;

            if (SpanEditModeValue.innerHTML === "False") {
                SwitchElementsEditMode(false);
                EditingSteps = false;
                return;
            }

            SwitchElementsEditMode(true);
            EditingSteps = true;
            return;
        })
        .catch(err => console.error("Error loading the test case:", err));


}

function ShowSuite(suiteID) {
    fetch(`/get_suite_html/${suiteID}`)
        .then(response => response.text())
        .then(html => { document.getElementById("details-pane").innerHTML = html; })
        .catch(err => console.error("Error loading the suite:", err));
}


document.getElementById("details-pane").addEventListener("click", function (event) {
    if (!event.target) return false;
    let error_message = "";
    let route = "";
    let send_data = {};
    let clickedid = "0"
    const tree = $('#testTree').jstree(true);
    let refresh_test_case = false;

    clickedid = "c_" + document.getElementById("details-pane").dataset.testId;
    if (document.getElementById("details-pane").dataset.suiteId) {
        clickedid = document.getElementById("details-pane").dataset.suiteId;
    }

    const node = tree.get_node(clickedid);

    switch (event.target.id) {

        case "btn-delete-suite":
            handleDelete(tree, node)
            break;

        case "btn-edit-suite":
            error_message = "Error loading new test form: ";
            // get current id if suite or test

            route = "/edit_test_case";
            if (node.type == "suite") route = "/edit_suite";

            send_data = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ id: node.id })
            }

            break;

        case "btn-new-testcase":
            error_message = "Error loading new test form: ";
            route = "/new_test_case_form";
            break;
        case "btn-new-suite":
            error_message = "Error loading new test form: ";
            route = "/new_suite_form";
            break;

        case "btn-new-version":
            route = "/new_test_case_version";
            send_data = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ id: node.id })
            }
            refresh_test_case = true;
            break;

        case "btn-delete-version":
            route = "/delete_testcase_version";
            send_data = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ id: node.id })
            }
            refresh_test_case = true;
            break;
        case "btn-add-new-step":
            showEditor({
                position: 'end',
            });
            break;

        case "btn-compare-version":
            error_message = "Error loading compare test form: ";

            route = "/compare_test_versions";

            send_data = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ id: node.id })
            }
            break;
        default:
            return;

    }

    if (!route) return;
    fetch(route, send_data)
        .then(res => res.text())
        .then(html => {
            this.innerHTML = html;
            if (refresh_test_case) ShowTestCase(clickedid);
        })

        .catch(err => console.error(error_message, err));


    return true;
});



function handleCompareVersionChange(event, testID, left_dropdown_current_value, right_dropdown_current_value) {

    const dropdownclicked = event.target.getAttribute('position');
    const changeVersionID = event.target.getAttribute('data-version-id');

    let left_dropdown_new_value = left_dropdown_current_value;
    let right_dropdown_new_value = right_dropdown_current_value;

    if (dropdownclicked == 'left') {
        left_dropdown_new_value = changeVersionID;
    }
    if (dropdownclicked == 'right') {
        right_dropdown_new_value = changeVersionID;
    }


    // Reload comparison view with new versions
    fetch('/compare_test_versions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ id: 'c_' + testID, left_compare: left_dropdown_new_value, right_compare: right_dropdown_new_value })
    })
        .then(res => res.text())
        .then(html => {
            document.getElementById("details-pane").innerHTML = html;
        })
        .catch(err => console.error("Error loading compare test form: ", err));
}

document.getElementById("details-pane").addEventListener("click", function (event) {

    if (!event.target || !event.target.classList.contains('version-option')) return;


    const testID = document.getElementById("details-pane").dataset.testId;


    // Check whether dropdown 1 or 2 exists
    if (document.getElementById('version-list-1') || document.getElementById('version-list-2')) {
        handleCompareVersionChange(
            event,
            testID,
            document.getElementById("versionDropdown-1").getAttribute("current-version"),
            document.getElementById("versionDropdown-2").getAttribute("current-version")
        );
        return; // Stop further execution
    }



    const versionId = event.target.getAttribute('data-version-id');
    fetch('/update_test_case_version', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-sWith': 'XMLHttpRequest' },
        body: JSON.stringify({ id: testID, version: versionId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                ShowTestCase(testID); // Reload the test case view
            } else {
                alert('Error updating test case version: ' + data.error);
            }
        })
        .catch(err => {
            console.error('Error updating test case version:', err);
            alert('An error occurred while updating the test case version.');
        });
});


document.addEventListener('DOMContentLoaded', function () {
    const header = document.getElementById('page-title');
    const leftpane = document.getElementById('left-pane');
    const rightpane = document.getElementById('right-pane');

    const scrollingPane = document.getElementById('right-pane');

    // Define the point at which the header should hide (e.g., 50 pixels)
    const scrollThreshold = 30;

    if (scrollingPane) {
        scrollingPane.addEventListener('scroll', () => {
            const hasScrolledPast = scrollingPane.scrollTop > scrollThreshold;
            header.classList.toggle('header-hidden', hasScrolledPast);
            leftpane.classList.toggle('hidden', hasScrolledPast);
            rightpane.classList.toggle('hidden', hasScrolledPast);
        });
    }
});

//--------------------------- steps --------------------
function CreateSortable(testcaseId) {
    if (user_level == 'viewer') return;

    const sortableList = document.getElementById('testStepslist');
    if (!sortableList) return;

    sortablehandler = Sortable.create(sortableList, {
        handle: '.bi-grip-vertical',
        animation: 150,
        dataIdAttr: 'data-step-id', // HTML attribute that is used by the `toArray()` method
        swapThreshold: 10, // Threshold of the swap zone
        direction: 'horizontal', // Direction of Sortable (will be detected automatically if not given)
        onChange: function () {

            const steps_positions = this.toArray();
            //As the steps position alteration have a timeout, a backup is need to save the last altartion in case of the page being reloaded or unloaded
            new_steps_order_payload = { id: testcaseId, steps: steps_positions };

            if (debounceTimer) clearTimeout(debounceTimer);

            debounceTimer = setTimeout(() => {
                HandlePositionChange(testcaseId, steps_positions);
            }, 2000);

        },
        onEnd: function () {

            const all_steps_positions = document.querySelectorAll('.stepNumber');

            for (let position = 0; position < all_steps_positions.length; position++) {
                all_steps_positions[position].innerHTML = position + 1;
            }

        }

    });


}


// This file is static/Scripts/test_specification.js

document.addEventListener('DOMContentLoaded', function () {

    const detailsPane = document.getElementById('details-pane');
    detailsPane.addEventListener('click', function (e) {

        // Check what was clicked using .closest()
        const addBtn = e.target.closest('.btn-add-after');
        const contentWrapperClicked = e.target.closest('.step-content-wrapper');
        const NumberClicked = e.target.closest('.stepNumber')
        const deleteBtn = e.target.closest('.btn-delete');
        const editBtn = e.target.closest('.btn-edit');
        const editStepsBtn = e.target.closest('.btn-check');
        const addStepEnd = e.target.closest("#btn-add-new-step");

        // --- Handle "Add Step After" Click ---
        if (addBtn) {

            if (!EditingSteps) return; //If the test is not in edidting mode

            e.preventDefault();
            const stepItem = addBtn.closest('.step-item');
            showEditor({
                position: 'after',
                referenceElement: stepItem
            });

            return;
        }

        // --- Handle "Edit Step" Click ---
        if (NumberClicked || contentWrapperClicked || editBtn) {

            if (!EditingSteps) return; //If the test is not in edidting mode

            e.preventDefault();
            let stepItem = "";
            if (contentWrapperClicked) {
                stepItem = contentWrapperClicked.closest('.step-item');
            }
            if (editBtn) {
                stepItem = editBtn.closest('.step-item');
            }

            showEditor({
                position: 'replace',
                referenceElement: stepItem
            });
            return;
        }

        // --- Handle "Delete Step" Click ---
        if (deleteBtn) {
            if (!EditingSteps) return; //If the test is not in edidting mode

            e.preventDefault();
            const stepItem = deleteBtn.closest('.step-item');
            const stepId = stepItem.dataset.stepId;

            if (confirm('Are you sure you want to delete this step?')) {
                console.log(`Deleting step with ID: ${stepId}`);
                HandleDeleteStep(stepId)
            }
            return;
        }

        if (editStepsBtn) {
            const EditingStepsButton = document.getElementById("btn-steps-editing");
            const SpanEditModeValue = document.querySelector('#editing-steps-value');

            if (EditingSteps) {
                SwitchElementsEditMode(false);

                EditingSteps = false;
                EditingStepsButton.innerHTML = "Enable edit mode";
                SpanEditModeValue.innerHTML = "False";

            } else {
                SwitchElementsEditMode(true);

                EditingSteps = true;
                EditingStepsButton.innerHTML = "Disable edit mode"
                SpanEditModeValue.innerHTML = "True";
            }


            fetch('/set_edit_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({
                    edit_mode: EditingSteps,
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert("Not possible to set the edit mode. Message: " + data.message);
                    }
                })
                .catch(err => {
                    console.error('Delete error:', err);
                });
        }

    });

    // @param {object} options - { position: 'after'|'replace'|'end', referenceElement?: HTMLElement }

});


function showEditor(options) {

    const editorTemplate = document.getElementById('editor-template');
    const detailsPane = document.getElementById('details-pane');

    // Delete the already exisiting editor
    const existingEditor = detailsPane.querySelector('.editor-form');
    if (existingEditor) {
        existingEditor.querySelector('.btn-cancel').click();
    }

    // Copy the template
    const editorClone = editorTemplate.content.cloneNode(true);
    const editorForm = editorClone.querySelector('.editor-form');

    // Find and assign unique IDs to textareas
    const actionsTextarea = editorForm.querySelector('.editor-actions');
    const resultsTextarea = editorForm.querySelector('.editor-results');
    const uniqueId = 'editor-' + Date.now();
    actionsTextarea.id = uniqueId + '-actions';
    resultsTextarea.id = uniqueId + '-results';

    // If editing, populate the editor with existing content
    if (!options.referenceElement && options.position != "end") return;
    if (options.position === 'replace') {
        const content = options.referenceElement.querySelector('.step-content-wrapper');
        actionsTextarea.value = content.querySelector('.Actions').innerHTML;
        resultsTextarea.value = content.querySelector('.Results').innerHTML;

        options.referenceElement.classList.add('d-none');
    }

    if (options.position === 'after' || options.position === 'replace') {
        options.referenceElement.after(editorForm);
    } else {
        const listContainer = detailsPane.querySelector('#testStepslist');
        if (listContainer) listContainer.append(editorForm);
    }

    // Initialize TinyMCE on the newly added textareas
    const commonConfig = {
        height: 250,
        menubar: true,
        promotion: false,
        resize: true,
        branding: false,
        plugins: [
            'advlist', 'autolink', 'link', 'lists', 'charmap', 'preview',
            'searchreplace', 'wordcount', 'visualblocks', 'visualchars', 'code', 'fullscreen',
            'insertdatetime', 'table', 'help', 'autoresize'
        ],
        toolbar: 'undo redo | bold italic | alignleft aligncenter alignright alignjustify | forecolor backcolor',
        menu: {
            edit: { title: 'Edit', items: 'undo redo | cut copy paste pastetext | selectall | searchreplace' },
            view: { title: 'View', items: 'code suggestededits revisionhistory | visualaid visualchars visualblocks | spellchecker | preview fullscreen | showcomments' },
            insert: { title: 'Insert', items: 'link addcomment pageembed codesample | math | charmap hr | nonbreaking tableofcontents | insertdatetime' },
            format: { title: 'Format', items: 'bold italic underline strikethrough superscript subscript codeformat | styles blocks fontfamily fontsize align lineheight | forecolor backcolor | language | removeformat' },
            tools: { title: 'Tools', items: 'code | wordcount' },
            table: { title: 'Table', items: 'inserttable | cell row column | advtablesort | tableprops deletetable' },
            help: { title: 'Help', items: 'help' }
        },
        menubar: ' edit | view | insert | format | tools | table | help',
        link_default_target: '_blank',
        autoresize_bottom_margin: 10,
        max_height: 500,
        min_height: 100,
        table_border_widths: [
            { title: 'small', value: '2px' },
            { title: 'medium', value: '3px' },
            { title: 'large', value: '6px' },
        ],
        help_accessibility: false,
        table_border_widths: [
            { title: '1px', value: '2px' },
            { title: '2px', value: '3px' },
            { title: '3px', value: '4px' },
            { title: '4px', value: '5px' },
            { title: '5px', value: '6px' }
        ],

    };

    tinymce.init({
        ...commonConfig,
        selector: `#${actionsTextarea.id}`,
        license_key: 'gpl',
    });

    tinymce.init({
        ...commonConfig,
        selector: `#${resultsTextarea.id}`,
        license_key: 'gpl',
    });

    // Handle Cancel button click
    editorForm.querySelector('.btn-cancel').addEventListener('click', () => {
        tinymce.remove(`#${actionsTextarea.id}`);
        tinymce.remove(`#${resultsTextarea.id}`);
        editorForm.remove();


        if (options.position === 'replace') options.referenceElement.classList.remove('d-none');
        StepAlreadyClicked = true
    });

    // Handle Save button click
    editorForm.querySelector('.btn-save').addEventListener('click', () => {
        // const ExistingStep = options.position === 'replace' ? true : false;

        //The replace is used to enlarge the default border size, because the the default one is not visible
        let newActions = tinymce.get(actionsTextarea.id).getContent().replaceAll("<td>", "<td style='border-width: 2px;'>");
        let newResults = tinymce.get(resultsTextarea.id).getContent().replaceAll("<td>", "<td style='border-width: 2px;'>");

        //closes the tinymce
        editorForm.querySelector('.btn-cancel').click();

        //Enters in the if statement only a test is being edit
        if (options.position === 'replace' ? true : false) {
            HandleEditStep(
                options.referenceElement.dataset.stepId,
                newActions,
                newResults,
                options.referenceElement
            );
            return;
        }

        const stepID = options.referenceElement ? options.referenceElement.dataset.stepId : false;

        HandleSaveStep(
            stepID,
            newActions,
            newResults,
        )

    });
}

function HandleDeleteStep(StepID) {
    const testID = document.getElementById("details-pane").dataset.testId;

    fetch('/delete_step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({
            step_id: StepID,
            test_id: testID
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                ShowTestCase(testID)
            } else {
                alert("Not possible to delete the step. Message: " + data.message);
            }
        })
        .catch(err => {
            console.error('Delete error:', err);
            alert("Error contacting server.");
        });

    return;
}

function HandleSaveStep(previousStepId, Actions, Results) {

    const testID = document.getElementById("details-pane").dataset.testId;

    let data = {
        test_id: testID,
        actions_data: Actions,
        results_data: Results,
        previous_step_id: previousStepId
    }


    fetch('/new_step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Not possible to create the new step. Message: " + data.message);
            } else {
                ShowTestCase(testID)
            }
        })
        .catch(err => {
            console.error('Delete error:', err);
            alert("Error contacting server.");
        });

    return;
}

function HandleEditStep(stepID, Actions, Results, StepElement) {

    fetch('/save_step_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({
            id: stepID,
            actions_data: Actions,
            results_data: Results
        })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Not possible to save the step: " + stepID + ". Message: " + data.message);
            } else { //if success
                StepElement.querySelector(".Actions").innerHTML = Actions
                StepElement.querySelector(".Results").innerHTML = Results
            }
        })
        .catch(err => {
            console.error('Delete error:', err);
            alert("Error contacting server.");
        });

    return;
}

function SwitchElementsEditMode(EnableEditMode) {
    if (user_level == 'viewer') return;

    const editStepButtons = document.querySelectorAll('.btn-edit');
    const deleteStepButtons = document.querySelectorAll('.btn-delete');
    const addtepButtons = document.querySelectorAll('.btn-add-after');
    const addStepEndButton = document.querySelectorAll("#btn-add-new-step");
    const EditingStepsButton = document.getElementById("btn-steps-editing");
    const OrderStepGrip = document.querySelectorAll(".bi-grip-vertical");


    if (EnableEditMode) {
        editStepButtons.forEach(button => { button.removeAttribute('hidden') });
        deleteStepButtons.forEach(button => { button.removeAttribute('hidden') });
        addtepButtons.forEach(button => { button.removeAttribute('hidden') });
        addStepEndButton.forEach(button => { button.removeAttribute('hidden') });
        OrderStepGrip.forEach(button => { button.removeAttribute('hidden') });
        EditingStepsButton.removeAttribute("check");
        sortablehandler.option("disabled", false);
        return;
    }

    editStepButtons.forEach(button => { button.setAttribute('hidden', 'true') });
    deleteStepButtons.forEach(button => { button.setAttribute('hidden', 'true') });
    addtepButtons.forEach(button => { button.setAttribute('hidden', 'true') });
    addStepEndButton.forEach(button => { button.setAttribute('hidden', 'true') });
    OrderStepGrip.forEach(button => { button.setAttribute('hidden', 'true') });
    EditingStepsButton.setAttribute("check", "true");

    sortablehandler.option("disabled", true);
    return;
}

function HandlePositionChange(testcaseId, new_steps_order) {

    fetch('/reorder_steps', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ id: testcaseId, steps: new_steps_order })
    })
        .then(response => response.json())
        .then(data => {
            //As the steps position were already changed, it is not necessary to save this payload
            new_steps_order_payload = null;

            if (!data.success) {
                alert("reorder failed: " + data.error);
            } else {
                const currentID = document.getElementById("details-pane").dataset.testId;
                if (currentID != testcaseId) return;

                ShowTestCase(testcaseId);
            }
        })
        .catch(err => {
            console.error('reorder error:', err);
            alert("Error contacting server.");
        });
}

window.addEventListener("beforeunload", () => {

    //Handles sending the last position saved from the step ordr altetion
    if (new_steps_order_payload) {
        const steps = new Blob(
            [JSON.stringify(new_steps_order_payload)],
            { type: 'application/json' }
        );

        navigator.sendBeacon("/reorder_steps", steps);
    }


});

//context menu handler
document.addEventListener('DOMContentLoaded', function () {

    const listContainer = document.getElementById('details-pane');
    const contextMenu = document.getElementById('step-context-menu');
    let currentStepElement = null; // To store which step was clicked

    // Show the context menu on right-click inside the list
    listContainer.addEventListener('contextmenu', function (e) {
        const targetStep = e.target.closest('.step-item');
        if (!EditingSteps) return; //If the test is not in editing mode

        if (targetStep) {
            //Handles the context menu exhbition considering the window dimensions 
            e.preventDefault();
            currentStepElement = targetStep;

            const windowHeight = window.innerHeight;
            const windowWidth = window.innerWidth;
            const menuHeight = contextMenu.offsetHeight;
            const menuWidth = contextMenu.offsetWidth;

            let topPosition = e.clientY;
            if ((e.clientY + menuHeight) > windowHeight) {
                topPosition = e.clientY - menuHeight;
            }

            let leftPosition = e.clientX;
            if ((e.clientX + menuWidth) > windowWidth) {
                leftPosition = e.clientX - menuWidth;
            }
            contextMenu.style.top = `${topPosition}px`;
            contextMenu.style.left = `${leftPosition}px`;
            contextMenu.classList.add('show');
        }
    });

    // Hide the menu when clicking anywhere else on the page
    window.addEventListener('click', function () {
        if (contextMenu.classList.contains('show')) {
            contextMenu.classList.remove('show');
        }
    });

    // Handle clicks on the menu action items
    contextMenu.addEventListener('click', function (e) {
        e.preventDefault();
        const action = e.target.closest('.dropdown-item')?.dataset.action;

        let stepItem = currentStepElement.closest('.step-item');
        if (action && currentStepElement) {

            switch (action) {
                case 'edit':
                    if (!EditingSteps) return; //If the test is not in edidting mode

                    e.preventDefault();

                    showEditor({
                        position: 'replace',
                        referenceElement: stepItem
                    });
                    break;
                case 'copy':
                    stepid_clipboard = stepItem.dataset.stepId;
                    break;
                case 'paste':

                    if (!stepid_clipboard) break;

                    const testID = document.getElementById("details-pane").dataset.testId;
                    fetch('/copy_step', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                        body: JSON.stringify({
                            copied_step_id: stepid_clipboard,
                            test_id: testID,
                            clicked_step_id: stepItem.dataset.stepId
                        })
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (!data.success) {
                                alert("Rename failed: " + data.message);
                            } else {
                                ShowTestCase(testID);
                            }
                        })
                        .catch(err => {
                            console.error('Rename error:', err);
                            alert("Error contacting server.");
                        });

                    stepid_clipboard = null;
                    break;
                case 'delete':
                    if (!EditingSteps) return; //If the test is not in edidting mode

                    e.preventDefault();

                    const stepId = stepItem.dataset.stepId;

                    if (confirm('Are you sure you want to delete this step?')) {
                        console.log(`Deleting step with ID: ${stepId}`);
                        HandleDeleteStep(stepId)
                    }
                    break;
                case 'add':

                    if (!EditingSteps) return; //If the test is not in edidting mode

                    e.preventDefault();
                    showEditor({
                        position: 'after',
                        referenceElement: stepItem
                    });

                    break;
            }
        }

        contextMenu.classList.remove('show');
    });
});