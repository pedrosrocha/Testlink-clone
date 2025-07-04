document.getElementById('reset-password-form').addEventListener('submit', function (e) {
    let isValid = true;

    const password = document.getElementById('newPassword').value;
    const errorSpan = document.getElementById('newPassword-error');

    //erases previous errors
    errorSpan.textContent = '';
    errorSpan.style.display = 'none';

    //check if the password has at least 6 digits
    if (password.length < 6) {
        errorSpan.textContent = "Password must have at least 6 characters"
        errorSpan.style.display = 'inline'
        isValid = false;
    }


    if (!isValid) {
        e.preventDefault(); //prevents form submission
    }
});