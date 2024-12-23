const formOpenBtn = document.querySelector("#form-open"),
  home = document.querySelector(".home"),
  formContainer = document.querySelector(".form_container"),
  formCloseBtn = document.querySelector(".form_close"),
  signupBtn = document.querySelector("#signup"), // Points to Signup button
  loginBtn = document.querySelector("#login"), // Points to Login button
  pwShowHide = document.querySelectorAll(".pw_hide");

// Open form on button click
formOpenBtn.addEventListener("click", () => {
  home.classList.add("show");
});

// Close form on close button click
formCloseBtn.addEventListener("click", () => {
  home.classList.remove("show");
});

pwShowHide.forEach(icon => {
    icon.addEventListener("click", () => {
        let getPwInput = icon.parentElement.querySelector("input");
        if (getPwInput.type === "password"){
            getPwInput.type = "text";
            icon.classList.replace("uil-eye-slash", "uil-eye");


        } else {
            getPwInput.type = "password";
            icon.classList.replace("uil-eye", "uil-eye-slash");

        }
    });
});

// Switch to signup form
signupBtn.addEventListener("click", (e) => {
  e.preventDefault();
  formContainer.classList.add("active");
});

// Switch back to login form
loginBtn.addEventListener("click", (e) => {
  e.preventDefault();
  formContainer.classList.remove("active");
});

//----------------------------------------------------------------------------------------------
// redirection to another page
// For login
document.querySelector(".login_form form").addEventListener("submit", (e) => {
    e.preventDefault(); // Prevent form submission
    // Add your login logic here (e.g., check credentials)

    // Redirect to dashboard.html after successful login
    window.location.href = "2HTML.html";
});

// For signup
document.querySelector(".signup_form form").addEventListener("submit", (e) => {
    e.preventDefault(); // Prevent form submission
    // Add your signup logic here (e.g., create new user)

    // Redirect to welcome.html after successful signup
    window.location.href = "2HTML.html";
});



