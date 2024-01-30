const alertPlaceholder = document.getElementById('alert-placeholder');
const showAlert = (message, type) => {
    let wrapper = document.createElement('div');
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible shadow-lg rounded fade show" role="alert">`,
        `   <div>${message}</div>`,
        `   <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`,
        `</div>`
    ].join('');
    alertPlaceholder.append(wrapper);

    setTimeout(() => {
        alertPlaceholder.innerHTML = '';
    }, 5000);
}

const previewImage = () => {
    const fileInput = document.getElementById('artwork');
    let preview = document.getElementById('artwork-preview');

    if (fileInput.files && fileInput.files[0]) {
        let reader = new FileReader();

        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.classList.remove('d-none');
        };

        reader.readAsDataURL(fileInput.files[0]);
    } else {
        preview.classList.add('d-none');
        preview.src = '';
    }
}

const loadPreset = (e, endpoint, presetId) => {
    if (presetId === "Select preset...") {
        return;
    }

    e.preventDefault();
    fetch(endpoint + '?preset-id=' + presetId)
        .then(response => {
            if (response.status === 200) {
                return response.json();
            } else {
                response.text().then(text => {
                    showAlert(text, 'danger');
                });
            }
        })
        .then(data => {
            let preview;
            if (data) {
                for (const [key, value] of Object.entries(data)) {
                    let input = document.getElementById(key.replace('_', '-'));

                    if (input && value) {
                        if (key === 'artwork') {
                            preview = document.getElementById('artwork-preview');
                            preview.src = value;
                            preview.classList.remove('d-none');
                            document.getElementById('artwork-name').value = value;
                        } else {
                            input.value = value;
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.error('Network error: ', error);
            showAlert('Network error', 'warning');
        });
}

document.getElementById('reset-button').addEventListener('click', function () {
    document.getElementById('metadata-form').reset();
    document.getElementById('artwork-preview').classList.add('d-none');
});

document.getElementById('submit-preset').addEventListener('click', function () {
    const originalText = this.innerHTML;
    this.setAttribute('disabled', 'disabled');
    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>Loading...';

    const metadataForm = document.getElementById('metadata-form');
    let formData = new FormData(metadataForm);

    const artworkInput = document.getElementById('artwork');
    if (artworkInput && artworkInput.files[0]) {
        formData.append('artwork', artworkInput.files[0]);
    }

    fetch(this.getAttribute('data-action'), {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (response.status === 201) {
                showAlert('Preset created/updated successfully', 'success');
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
            showAlert('Network error, try again later', 'warning');
        });
});

document.getElementById('remove-artwork').addEventListener('click', function () {
    document.getElementById('artwork-preview').classList.add('d-none');
    document.getElementById('artwork').value = '';
});
