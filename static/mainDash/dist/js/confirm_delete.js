window.confirmDelete = (function () {
    var pendingAction = null;
    var initialized = false;

    function showToast(message, alertType) {
        var toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        var toastHtml = `
            <div class="toast align-items-center text-bg-${alertType} border-0"
                 role="alert" aria-live="assertive" aria-atomic="true"
                 data-bs-autohide="true" data-bs-delay="3000">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto"
                            data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>`;

        toastContainer.innerHTML = toastHtml;
        var toastEl = toastContainer.querySelector('.toast');
        tabler.Toast.getOrCreateInstance(toastEl).show();
    }

    function init() {
        if (initialized) return;
        initialized = true;

        var confirmBtn = document.getElementById('confirm-delete-btn');
        if (!confirmBtn) {
            console.error('confirmDelete: #confirm-delete-btn not found.');
            return;
        }

        confirmBtn.addEventListener('click', function () {
            if (!pendingAction) return;
            var action = pendingAction;
            pendingAction = null;

            var btn     = document.getElementById('confirm-delete-btn');
            var label   = document.getElementById('confirm-delete-label');
            var spinner = document.getElementById('confirm-delete-spinner');

            // Show spinner, disable button
            btn.disabled = true;
            label.textContent = 'Deleting...';
            spinner.style.display = 'inline-block';

            fetch(action.url, {
                method: 'POST',
                headers: { 'X-CSRFToken': action.csrfToken },
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                // Close modal first
                var dismissBtn = document.querySelector('#confirm-delete-modal [data-bs-dismiss="modal"]');
                if (dismissBtn) dismissBtn.click();

                if (data.success) {
                    if (data.message) showToast(data.message, data.alert_type || 'success');
                    if (data.redirectUrl) {
                        setTimeout(function () { window.location.href = data.redirectUrl; }, 1500);
                    }
                    if (action.onSuccess) action.onSuccess(data);
                } else {
                    if (data.message) showToast(data.message, data.alert_type || 'danger');
                    if (action.onError) action.onError(data);
                }
            })
            .catch(function (err) {
                console.error('confirmDelete request failed:', err);
                var dismissBtn = document.querySelector('#confirm-delete-modal [data-bs-dismiss="modal"]');
                if (dismissBtn) dismissBtn.click();
                showToast('An error occurred. Please try again.', 'danger');
                if (action.onError) action.onError({ error: 'Request failed.' });
            })
            .finally(function () {
                btn.disabled = false;
                label.textContent = 'Yes, Delete';
                spinner.style.display = 'none';
            });
        });
    }

    return function confirmDelete(options) {
        init();

        document.getElementById('confirm-delete-title').textContent =
            options.title || 'Are you sure?';
        document.getElementById('confirm-delete-message').textContent =
            options.message || 'This action cannot be undone.';

        pendingAction = {
            url: options.url,
            csrfToken: options.csrfToken,
            onSuccess: options.onSuccess,
            onError: options.onError,
        };

        document.getElementById('open-confirm-delete-trigger').click();
    };
})();