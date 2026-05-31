// ===============================
// AI CRM DASHBOARD CHARTS
// ===============================

// Wait until page fully loads

document.addEventListener("DOMContentLoaded", function () {

    // ===============================
    // LEAD PRIORITY BAR CHART
    // ===============================

    const leadChartCanvas = document.getElementById('leadChart');

    if (leadChartCanvas) {

        new Chart(leadChartCanvas, {

            type: 'bar',

            data: {

                labels: [
                    'High Priority',
                    'Medium Priority',
                    'Low Priority'
                ],

                datasets: [{

                    label: 'Lead Count',

                    data: [

                        parseInt(
                            leadChartCanvas.dataset.high
                        ),

                        parseInt(
                            leadChartCanvas.dataset.medium
                        ),

                        parseInt(
                            leadChartCanvas.dataset.low
                        )

                    ],

                    borderWidth: 1

                }]

            },

            options: {

                responsive: true,

                plugins: {

                    legend: {
                        display: true
                    }

                },

                scales: {

                    y: {
                        beginAtZero: true
                    }

                }

            }

        });

    }


    // ===============================
    // LEAD SOURCE PIE CHART
    // ===============================

    const sourceChartCanvas = document.getElementById('sourceChart');

    if (sourceChartCanvas) {

        new Chart(sourceChartCanvas, {

            type: 'pie',

            data: {

                labels: [
                    'Website',
                    'Instagram',
                    'Facebook',
                    'Google Forms',
                    'Manual'
                ],

                datasets: [{

                    label: 'Lead Sources',

                    data: [

                        parseInt(
                            sourceChartCanvas.dataset.website
                        ),

                        parseInt(
                            sourceChartCanvas.dataset.instagram
                        ),

                        parseInt(
                            sourceChartCanvas.dataset.facebook
                        ),

                        parseInt(
                            sourceChartCanvas.dataset.google
                        ),

                        parseInt(
                            sourceChartCanvas.dataset.manual
                        )

                    ],

                    borderWidth: 1

                }]

            },

            options: {

                responsive: true

            }

        });

    }


    // ===============================
    // LIVE CLOCK
    // ===============================

    const liveClock = document.getElementById("liveClock");

    if (liveClock) {

        setInterval(() => {

            const now = new Date();

            liveClock.innerHTML =
                now.toLocaleTimeString();

        }, 1000);

    }


    // ===============================
    // SEARCH INPUT AUTO FOCUS
    // ===============================

    const searchInput =
        document.querySelector(
            'input[name="search"]'
        );

    if (searchInput) {

        searchInput.focus();

    }


    // ===============================
    // CONFIRM DELETE LEAD
    // ===============================

    const deleteButtons =
        document.querySelectorAll(
            '.delete-btn'
        );

    deleteButtons.forEach(button => {

        button.addEventListener(
            'click',
            function (event) {

                const confirmDelete =
                    confirm(
                        "Are you sure you want to delete this lead?"
                    );

                if (!confirmDelete) {

                    event.preventDefault();

                }

            }
        );

    });


    // ===============================
    // TASK COMPLETE SUCCESS MESSAGE
    // ===============================

    const completeButtons =
        document.querySelectorAll(
            '.complete-btn'
        );

    completeButtons.forEach(button => {

        button.addEventListener(
            'click',
            function () {

                alert(
                    "Task marked as completed!"
                );

            }
        );

    });


    // ===============================
    // TABLE ROW HOVER EFFECT
    // ===============================

    const tableRows =
        document.querySelectorAll('table tr');

    tableRows.forEach(row => {

        row.addEventListener(
            'mouseenter',
            function () {

                this.style.transition =
                    '0.2s';

            }
        );

    });

});