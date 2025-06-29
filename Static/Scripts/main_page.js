

//window.addEventListener('DOMContentLoaded', function () {
//    const select = document.getElementById('project-selector-form');
//    const selectedProjectId = select.value;
//
//    console.log("Selected project on load:", selectedProjectId);
//
//    fetch('/SelectProject', {
//        method: 'POST',
//        headers: {
//            'Content-Type': 'application/json',
//            'X-Requested-With': 'XMLHttpRequest'
//        },
//        body: JSON.stringify({ project_id: selectedProjectId })
//    })
//    .then(response => response.json())
//    .then(data => {
//        if (data.success) {
//            //console.log("Initial project selected:", selectedProjectId);
//        }
//    });
//});