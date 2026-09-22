// This file contains JavaScript code for client-side interactivity, including form validation and dynamic content updates.

document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("form");
    const cgpaInput = document.querySelector("input[name='cgpa']");
    const projectsInput = document.querySelector("input[name='projects']");

    form.addEventListener("submit", function(event) {
        let valid = true;

        // Clear previous error messages
        clearErrors();

        // Validate CGPA
        if (!validateCGPA(cgpaInput.value)) {
            showError(cgpaInput, "Please enter a valid CGPA (0.0 - 4.0).");
            valid = false;
        }

        // Validate Projects
        if (projectsInput.value.trim() === "") {
            showError(projectsInput, "Projects field cannot be empty.");
            valid = false;
        }

        if (!valid) {
            event.preventDefault(); // Prevent form submission if validation fails
        }
    });

    function validateCGPA(cgpa) {
        const cgpaFloat = parseFloat(cgpa);
        return !isNaN(cgpaFloat) && cgpaFloat >= 0.0 && cgpaFloat <= 4.0;
    }

    function showError(input, message) {
        const error = document.createElement("div");
        error.className = "error-message";
        error.textContent = message;
        input.parentNode.insertBefore(error, input.nextSibling);
    }

    function clearErrors() {
        const errorMessages = document.querySelectorAll(".error-message");
        errorMessages.forEach(error => error.remove());
    }
});