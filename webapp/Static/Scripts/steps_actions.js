// Contains all logic related to test steps, including sorting,
// editing, creating, deleting, and context menus.

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


async function showEditor(options) {

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
        const step = await get_step(options.referenceElement.dataset.stepId);

        actionsTextarea.value = step.step_action;
        resultsTextarea.value = step.expected_value;

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
            }
            const testID = document.getElementById("details-pane").dataset.testId;
            ShowTestCase(testID);
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
    async function copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    }

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
                case 'ghost':

                    const position = stepItem.dataset.stepPosition;
                    const testcaseID = document.getElementById("details-pane").dataset.testId;
                    const currentVersion = document.getElementsByClassName("current-version")[0].dataset.currentVersion;
                    copyToClipboard('[ghost]"Step":' + position + ',"TestCase":' + testcaseID + ',"Version":' + currentVersion + '[/ghost]');
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


async function get_step(step_id) {
    const params = new URLSearchParams();
    params.append('step', step_id);

    try {
        const response = await fetch(`/get_step?${params.toString()}`);

        if (!response.ok) {
            // If the server responded with an error (like 404 or 500)
            throw new Error(`Server error: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.success) {
            alert("Could not get step info. Message: " + data.error);
            return null; // Return null on application-level error
        }

        // This is what the function will return after it's all done
        return data.step;


    } catch (err) {
        console.error('Fetch error:', err);
        return null; // Return null on network or other errors
    }
}


