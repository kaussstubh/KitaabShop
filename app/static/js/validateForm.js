function validate() {
    // Get field values
    var pass = document.getElementById("password").value;
    var cpass = document.getElementById("cpassword").value;
    var email = document.querySelector('input[name="email"]').value;
    var phone = document.querySelector('input[name="phone"]').value;

    // Password match validation
    if (pass !== cpass) {
        alert("Passwords do not match");
        return false;
    }

    // Password strength validation
    if (pass.length < 8 || !/\d/.test(pass) || !/[!@#$%^&*]/.test(pass)) {
        alert("Password must be at least 8 characters long and include at least one number and one special character (!@#$%^&*)");
        return false;
    }

    // Email format validation
    var emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    if (!emailPattern.test(email)) {
        alert("Please enter a valid email address");
        return false;
    }

    // Phone number validation (digits only)
    var phonePattern = /^[0-9]+$/;
    if (!phonePattern.test(phone)) {
        alert("Phone number must contain digits only");
        return false;
    }

    // If everything is valid, return true to submit the form
    return true;
}
