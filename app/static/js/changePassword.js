function validate() {
    var newPassword = document.getElementById("newpassword").value;
    var confirmPassword = document.getElementById("cpassword").value;

    // Check if passwords match
    if (newPassword != confirmPassword) {
        alert("New password and confirm password do not match.");
        return false;
    }

    // Basic password strength validation
    if (newPassword.length < 8) {
        alert("Password must be at least 8 characters long.");
        return false;
    }

    return true;
}
