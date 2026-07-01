
window.confirmAction = (function () {
    var pendingAction = null;
    var initialized = false;

    function init() {
        if (initialized) return;
        initialized = true;

        var confirmBtn = document.getElementById('confirm-action-btn');
        if (!confirmBtn) {
            console.error('confirmAction: #confirm-action-btn not found.');
            return;
        }

        confirmBtn.addEventListener('click', function () {
            if (!pendingAction) return;
            var action = pendingAction;
            pendingAction = null;

            var btn = document.getElementById('confirm-action-btn');
            var label = document.getElementById('confirm-action-label');
            var spinner = document.getElementById('confirm-action-spinner');

            // Show spinner, disable button
            btn.disabled = true;
            label.textContent = action.processingLabel || 'Processing...';
            spinner.style.display = 'inline-block';

            fetch(action.url, {
                method: action.method || 'POST',
                headers: {
                    'X-CSRFToken': action.csrfToken,
                    'HX-Request': 'true',
                },
            })
            .then(function (res) { return res.text(); })
            .then(function (html) {
                var parser = new DOMParser();
                var doc = parser.parseFromString(html, 'text/html');

                var toastEl = doc.querySelector('.toast');
                if (toastEl) {
                    // Server responded — close modal now
                    var dismissBtn = document.querySelector('#confirm-action-modal [data-bs-dismiss="modal"]');
                    if (dismissBtn) dismissBtn.click();

                    var redirectUrl = toastEl.getAttribute('data-redirect-url');
                    document.getElementById('toast-container').innerHTML = toastEl.outerHTML;
                    var liveToast = document.querySelector('#toast-container .toast');
                    tabler.Toast.getOrCreateInstance(liveToast).show();

                    if (redirectUrl) {
                        setTimeout(function () { window.location.href = redirectUrl; }, 1500);
                    }
                }

                if (action.onSuccess) action.onSuccess();
            })
            .catch(function (err) {
                console.error('confirmAction request failed:', err);
                var dismissBtn = document.querySelector('#confirm-action-modal [data-bs-dismiss="modal"]');
                if (dismissBtn) dismissBtn.click();
                if (action.onError) action.onError({ error: 'Request failed.' });
            })
            .finally(function () {
                btn.disabled = false;
                spinner.style.display = 'none';
            });
        });
    }

    return function confirmAction(options) {
        init();

        document.getElementById('confirm-action-title').textContent =
            options.title || 'Are you sure?';
        document.getElementById('confirm-action-message').textContent =
            options.message || 'This action cannot be undone.';

        // Set confirm button label and colour
        var confirmBtn = document.getElementById('confirm-action-btn');
        var label = document.getElementById('confirm-action-label');
        label.textContent = options.confirmLabel || 'Confirm';
        confirmBtn.className = 'btn ' + (options.btnClass || 'btn-primary');

        pendingAction = {
            url: options.url,
            method: options.method || 'POST',
            csrfToken: options.csrfToken,
            confirmLabel: options.confirmLabel || 'Confirm',
            processingLabel: options.processingLabel || 'Processing...',
            onSuccess: options.onSuccess,
            onError: options.onError,
        };

        document.getElementById('open-confirm-action-trigger').click();
    };
})();