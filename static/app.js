const alertPlaceholder = document.getElementById('alert-placeholder');
const showAlert = (message, type) => {
    wrapper = document.createElement('div');
    wrapper.innerHTML = [
      `<div class="alert alert-${type} alert-dismissible" role="alert">`,
      `   <div>${message}</div>`,
      `   <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`,
      `</div>`
    ].join('');
    alertPlaceholder.append(wrapper);

    setTimeout(() => {
        alertPlaceholder.innerHTML = '';
    }, 3000);
}

document.getElementById('reset-button').addEventListener('click', function() {
    document.getElementById('metadata-form').reset();
});

document.getElementById('submit-preset').addEventListener('click', function() {
    let originalText = this.innerHTML;
    this.setAttribute('disabled', 'disabled');
    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>Loading...';

    var metadataForm = document.getElementById('metadata-form');
    var formData = new FormData(metadataForm);

    var artworkInput = document.getElementById('artwork');
    if (artworkInput && artworkInput.files[0]) {
        formData.append('artwork', artworkInput.files[0]);
    }

    fetch(this.getAttribute('data-action'), {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.status === 201) {
            showAlert('Preset created successfully', 'success');
        } else {
            response.text().then(text => {
                showAlert(text, 'danger');
            });
        }
    })
    .then(() => {
        this.removeAttribute('disabled');
        this.innerHTML = originalText;
    })
    .catch(error => {
        console.error('Network error: ', error);
        showAlert('Network error', 'warning');
    });
});

