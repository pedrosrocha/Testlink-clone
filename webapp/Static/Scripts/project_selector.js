document.getElementById('project-selector-form').addEventListener('change', function () {
    const projectId = this.value; //get value form the dropdown

    //console.log("Sending project ID:", projectId);
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
            //document.getElementById('feedback').textContent = "Project changed!";
        } else {
            alert("Something went wrong.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Error while changing project.");
    });
});
