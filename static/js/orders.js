document.addEventListener('DOMContentLoaded', () => {
    const cancelButtons = document.querySelectorAll('.cancel-button');
    const syncButtons = document.querySelectorAll('.sync-button');
    const confirmCancelButton = document.getElementById('confirmCancelButton');
    const cancelForm = document.getElementById('cancelForm');
    let currentOrderId = null;

    // Handle cancel button clicks to show modal and store order ID
    cancelButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentOrderId = button.dataset.orderId; // Use dataset.orderId (matches data-order-id)
            if (!currentOrderId || currentOrderId === 'undefined') {
                alert('Error: Invalid order ID');
                return;
            }
            // Show the confirmation modal
            const modal = new bootstrap.Modal(document.getElementById('confirmCancelModal'));
            modal.show();
        });
    });

    // Handle confirm button in modal to submit the cancel form
    if (confirmCancelButton) {
        confirmCancelButton.addEventListener('click', () => {
            if (currentOrderId) {
                // Set the form action with the correct order ID
                cancelForm.action = `/orders/${currentOrderId}/cancel`;
                cancelForm.submit();
            } else {
                alert('Error: No order ID selected');
            }
            // Hide the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('confirmCancelModal'));
            modal.hide();
        });
    }

    // Handle sync button clicks to show overlay and submit sync form
    syncButtons.forEach(button => {
        button.addEventListener('click', () => {
            showOverlay('Syncing orders...'); // Assumes showOverlay is defined elsewhere
            document.getElementById('syncForm').submit();
        });
    });
});