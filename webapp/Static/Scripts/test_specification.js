// Main script for the test specification page.
// Initializes global variables and fetches initial user data.

let currentSuiteId = null;
let currentTestCaseId = null;
let StepAlreadyClicked = false;
let EditingSteps = false;
var sortablehandler;

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