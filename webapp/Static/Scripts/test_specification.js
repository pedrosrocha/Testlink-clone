
const divider = document.getElementById('divider');


let currentSuiteId = null;
let currentTestCaseId = null;
let StepAlreadyClicked = false;
let EditingSteps = false;
var sortablehandler;

let isResizing = false;

let clipboard = {
    node: null,
    action: null // 'copy' or 'cut'
};


divider.addEventListener('mousedown', (e) => {
    isResizing = true;
    document.body.style.cursor = 'col-resize';
});

document.addEventListener('mousemove', (e) => {
    const leftColumn = document.getElementById('left-column');

    if (!isResizing) return;

    const newWidth = e.clientX;

    // No need to check min/max here since it's handled by the CSS
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


            CreateSortable();



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
            showEditor({ position: 'end' });
            return;
        default:
            return;

    }

    fetch(route, send_data)
        .then(res => res.text())
        .then(html => {
            this.innerHTML = html;
            if (refresh_test_case) ShowTestCase(clickedid);
        })

        .catch(err => console.error(error_message, err));


    return true;
});



document.getElementById("details-pane").addEventListener("click", function (event) {
    //chnges the current test version
    if (!event.target || !event.target.classList.contains('version-option')) return;

    const testID = document.getElementById("details-pane").dataset.testId;
    const versionId = event.target.getAttribute('data-version-id');


    fetch('/update_test_case_version', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ id: testID, version: versionId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                ShowTestCase(testID); // Reload the test case view
            } else {
                alert('Error updating suite: ' + data.error);
            }
        })
        .catch(err => {
            console.error('Error updating suite:', err);
            alert('An error occurred while updating the suite.');
        });

    ShowTestCase(testID);
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
function CreateSortable() {
    const sortableList = document.getElementById('testStepslist');


    if (sortableList) {
        sortablehandler = Sortable.create(sortableList, {
            handle: '.bi-grip-vertical',
            animation: 150
        });
    }

}


// This file is static/Scripts/test_specification.js

document.addEventListener('DOMContentLoaded', function () {

    // --- EVENT DELEGATION FOR DYNAMIC CONTENT ---


    const detailsPane = document.getElementById('details-pane');
    // Attach ONE listener to the parent container
    detailsPane.addEventListener('click', function (e) {

        // Check what was clicked using .closest()
        const addBtn = e.target.closest('.btn-add-after');
        const contentWrapperClicked = e.target.closest('.step-content-wrapper');
        const NumberClicked = e.target.closest('.stepNumber')
        const deleteBtn = e.target.closest('.btn-delete');
        const editBtn = e.target.closest('.btn-edit');
        const editStepsBtn = e.target.closest('.btn-check');

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
            } else {
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
    if (options.position === 'replace') {
        const content = options.referenceElement.querySelector('.step-content-wrapper');
        actionsTextarea.value = content.querySelector('.stepActions').innerHTML;
        resultsTextarea.value = content.querySelector('.stepResults').innerHTML;

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

    };

    tinymce.init({
        ...commonConfig,
        selector: `#${actionsTextarea.id}`,
        license_key: 'gpl',
    });

    tinymce.init({
        ...commonConfig,
        selector: `#${resultsTextarea.id}`,
        license_key: 'gpl'
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

        //read the values written by the user
        const newActions = tinymce.get(actionsTextarea.id).getContent();
        const newResults = tinymce.get(resultsTextarea.id).getContent();

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
                StepElement.querySelector(".stepActions").innerHTML = Actions
                StepElement.querySelector(".stepResults").innerHTML = Results
            }
        })
        .catch(err => {
            console.error('Delete error:', err);
            alert("Error contacting server.");
        });

    return;
}

function SwitchElementsEditMode(EnableEditMode) {
    const editStepButtons = document.querySelectorAll('.btn-edit');
    const deleteStepButtons = document.querySelectorAll('.btn-delete');
    const addtepButtons = document.querySelectorAll('.btn-add-after');
    const addStepEndButton = document.querySelectorAll("#btn-add-new-step");
    const EditingStepsButton = document.getElementById("btn-steps-editing");


    if (EnableEditMode) {
        editStepButtons.forEach(button => { button.removeAttribute('hidden') });
        deleteStepButtons.forEach(button => { button.removeAttribute('hidden') });
        addtepButtons.forEach(button => { button.removeAttribute('hidden') });
        addStepEndButton.forEach(button => { button.removeAttribute('hidden') });
        EditingStepsButton.removeAttribute("check");

        sortablehandler.option("disabled", false);
        return;
    }

    editStepButtons.forEach(button => { button.setAttribute('hidden', 'true') });
    deleteStepButtons.forEach(button => { button.setAttribute('hidden', 'true') });
    addtepButtons.forEach(button => { button.setAttribute('hidden', 'true') });
    addStepEndButton.forEach(button => { button.setAttribute('hidden', 'true') });
    EditingStepsButton.setAttribute("check", "true");
    sortablehandler.option("disabled", true);
    return;
}