/**
 * IT-Lend — main.js
 * JavaScript dùng chung toàn ứng dụng
 */

document.addEventListener('DOMContentLoaded', function () {

    // ── Sidebar Toggle ────────────────────────────────────────────
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar   = document.getElementById('sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('collapsed');
        });
    }

    // ── Auto-dismiss flash messages (5 giây) ─────────────────────
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Date validation: ngày trả phải sau ngày mượn ─────────────
    // (TODO Thành viên C: mở rộng logic này)
    const borrowDateInput = document.getElementById('borrowDate');
    const returnDateInput = document.getElementById('returnDate');

    if (borrowDateInput && returnDateInput) {
        borrowDateInput.addEventListener('change', function () {
            // Đặt min của ngày trả = ngày mượn + 1
            const selected = new Date(this.value);
            selected.setDate(selected.getDate() + 1);
            const minReturn = selected.toISOString().split('T')[0];
            returnDateInput.min = minReturn;

            // Reset ngày trả nếu đang chọn ngày trả <= ngày mượn
            if (returnDateInput.value && returnDateInput.value <= this.value) {
                returnDateInput.value = minReturn;
            }
        });
    }

    // ── Tooltip initialization (Bootstrap) ───────────────────────
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

});

