
document.addEventListener('DOMContentLoaded', function () {
    const projectSelector = document.getElementById('project-selector-form');

    if (projectSelector) {
        projectSelector.addEventListener('change', function () {
            const projectId = this.value; // Get value from the dropdown

            fetch('/SelectProject', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ project_id: projectId })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert("Something went wrong.");
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert("Error while changing project.");
                });
        });
    }
});