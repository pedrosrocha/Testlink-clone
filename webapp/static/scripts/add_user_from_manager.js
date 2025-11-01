document.getElementById('add-user-form').addEventListener('submit', function (e) {
    let isValid = true;

    // Clear previous messages first
    document.querySelectorAll('span[id$="-error"]').forEach(el => {
        el.style.display = 'none';
        el.textContent = '';
    });

    // Validate fields
    if (document.getElementById('username').value.trim() === '') {
        document.getElementById('username-error').textContent = "Username cannot be empty.";
        document.getElementById('username-error').style.display = "inline";
        isValid = false;
    }
    if (document.getElementById('email').value.trim() === '') {
        document.getElementById('email-error').textContent = "Email cannot be empty.";
        document.getElementById('email-error').style.display = "inline";
        isValid = false;
    }

    if (document.getElementById('password').value.length < 6) {
        document.getElementById('password-error').textContent = "Password must have at least 6 characters"
        document.getElementById('password-error').style.display = 'inline'
        isValid = false;
    }

    if (!isValid) {
        e.preventDefault();
    }
});