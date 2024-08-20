// Get the modal element
var modal = document.getElementById("searchPdfModal");

// Get the button that opens the modal
var btn = document.getElementById("searchPdfBtn");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks the button, open the modal
btn.onclick = function() {
    modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Handling form submission for search PDF
document.getElementById("searchPdfForm").onsubmit = function(event) {
    event.preventDefault();

    var formData = new FormData(this);
    var progressContainer = document.getElementById("progress-container");
    var progressBar = document.getElementById("progress-bar");
    var progressText = document.getElementById("progress-text");

    progressContainer.style.display = "block";

    function updateProgress() {
        fetch('/progress')
        .then(response => response.json())
        .then(data => {
            progressBar.value = data.progress;
            progressText.textContent = `Processed ${data.processed_files} of ${data.total_files} files.`;

            if (data.progress < 100) {
                setTimeout(updateProgress, 500);  // Update every 500ms
            }
        })
        .catch(error => console.error('Error fetching progress:', error));
    }

    updateProgress();  // Start updating progress

    fetch('/search_pdfs', {
        method: 'POST',
        body: formData
    }).then(response => {
        if (response.ok) {
            response.json().then(data => {
                window.location.href = '/search_results'; // Redirect to results page
            });
        } else {
            alert('Error occurred during search.');
        }
    }).catch(error => {
        console.error('Error:', error);
    });
};
