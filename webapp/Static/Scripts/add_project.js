document.getElementById('add-user-form').addEventListener('submit', function (e) {
    let isValid = true;

    // Clear previous messages first
    document.querySelectorAll('span[id$="-error"]').forEach(el => {
        el.style.display = 'none';
        el.textContent = '';
    });

    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;

    // Validate fields
    if (document.getElementById('project_name').value.trim() === '') {
        document.getElementById('project-name-error').textContent = "Project name cannot be empty.";
        document.getElementById('project-name-error').style.display = "inline";
        isValid = false;
    }

    // Date validation (if both dates are filled)
    if (startDate && endDate) {
        if (new Date(startDate) > new Date(endDate)) {
            alert("End date must be after or equal to start date.");
            isValid = false;
        }
    }


    if (!isValid) {
        e.preventDefault();
    }
});