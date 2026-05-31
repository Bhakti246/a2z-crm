// =========================
// CRM SYSTEM JS
// =========================

console.log("CRM System Loaded");


// =========================
// AUTO CLOSE ALERTS
// =========================

setTimeout(() => {

    let alerts = document.querySelectorAll('.alert');

    alerts.forEach((alert) => {

        alert.style.transition = "0.5s";

        alert.style.opacity = "0";

        setTimeout(() => {

            alert.remove();

        }, 500);

    });

}, 3000);


// =========================
// DELETE CONFIRMATION
// =========================

let deleteButtons = document.querySelectorAll('.btn-danger');

deleteButtons.forEach((button) => {

    button.addEventListener('click', (e) => {

        let confirmDelete = confirm(
            "Are you sure you want to delete this lead?"
        );

        if(!confirmDelete){

            e.preventDefault();

        }

    });

});


// =========================
// SEARCH INPUT FOCUS EFFECT
// =========================

let searchInput = document.querySelector(
    'input[name="search"]'
);

if(searchInput){

    searchInput.addEventListener('focus', () => {

        searchInput.style.borderColor = '#2563eb';

    });

}


// =========================
// SIMPLE DASHBOARD STATS ANIMATION
// =========================

let statNumbers = document.querySelectorAll('.stat-number');

statNumbers.forEach((number) => {

    let finalValue = parseInt(number.innerText);

    let startValue = 0;

    let duration = 30;

    let counter = setInterval(() => {

        startValue++;

        number.innerText = startValue;

        if(startValue >= finalValue){

            clearInterval(counter);

        }

    }, duration);

});


// =========================
// CURRENT YEAR
// =========================

let yearElement = document.querySelector('#currentYear');

if(yearElement){

    yearElement.innerText = new Date().getFullYear();

}