// Contains the logic for the details pane, including showing test cases/suites,
// handling form submissions, button clicks, and version comparisons.

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
                ShowTestCase(data.id)
            }
        })
        .catch(error => {
            console.error("Error contacting backend:", error);
            alert("Error contacting the server.");
        });

}


function ShowTestCase(testcaseId) {

    if ((typeof testcaseId === 'string' || testcaseId instanceof String) && testcaseId.startsWith("c")) {
        testcaseId = testcaseId.replace("c_", "");
    }


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
