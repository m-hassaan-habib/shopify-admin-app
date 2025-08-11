function showOverlay(text) {
    let overlay = document.getElementById('loadingOverlay');
    overlay.querySelector('.spinner-text').textContent = text;
    overlay.classList.add('active');
}

function hideOverlay() {
    let overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('active');
}