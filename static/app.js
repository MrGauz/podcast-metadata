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
        };

        reader.readAsDataURL(fileInput.files[0]);
    } else {
        preview.src = 'static/art_placeholder.png';
        document.getElementById('artwork-name').value = '';
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
    document.getElementById('artwork-preview').src = 'static/art_placeholder.png';
    document.getElementById('artwork-name').value = '';
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
    document.getElementById('artwork-preview').src = 'static/art_placeholder.png';
    document.getElementById('artwork').value = '';
    document.getElementById('artwork-name').value = '';
});

document.getElementById('metadata-form').addEventListener('submit', function (event) {
    event.preventDefault();

    const form = event.target;
    const button = document.getElementById('embed-audio-button');

    Array.from(form.elements).forEach(function (element) {
        if (element.id !== 'embed-audio-button') {
            element.disabled = true;
        }
    });
    button.classList.add('pe-none');

    button.innerHTML = '<span class="px-5" id="processing-step">Uploading file...</span>' +
        '<div class="progress w-100 mt-1" id="upload-progress-container" style="height: 5px;">' +
        '<div id="upload-progress-bar" class="progress-bar bg-warning progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0;" ' +
        'aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div></div>';
    const processingStep = document.getElementById('processing-step');
    const progressBar = document.getElementById('upload-progress-bar');

    const formData = new FormData();
    Array.from(form.elements).forEach(function (element) {
        if (element.name) {
            formData.append(element.name, element.files ? element.files[0] : element.value);
        }
    });

    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener('progress', function (e) {
        if (e.lengthComputable) {
            const percentComplete = Math.floor((e.loaded / e.total) * 100);
            progressBar.style.width = percentComplete + '%';
            progressBar.setAttribute('aria-valuenow', percentComplete.toString());
            if (percentComplete === 100) {
                processingStep.innerText = 'Embedding metadata...';
                processingStep.classList.replace('px-5', 'px-3');
            }
        }
    }, false);

    xhr.open('POST', form.action);
    xhr.onload = function () {
        Array.from(form.elements).forEach(function (element) {
            element.disabled = false;
        });
        button.classList.remove('pe-none');
        button.innerHTML = '<span class="mx-3 mx-md-5">Embed into audio</span>';

        let alert = '';
        let alertClass = 'alert-success';
        if (xhr.status === 200) {
            alert = 'File is being downloaded in the background...';
            form.target = 'download-iframe';
            form.submit();
        } else if (xhr.status >= 400 && xhr.status < 500) {
            alert = xhr.responseText;
            alertClass = 'alert-danger';
        } else if (xhr.status >= 500) {
            alert = 'We\'re having technical issues, please try again later.';
            alertClass = 'alert-danger';
        }
        if (alert) {
            document.getElementById('alert-placeholder').innerHTML = '<div class="alert alert-dismissible ' +
                'shadow-lg rounded fade show ' + alertClass + '" role="alert"><div>' + alert + '</div>' +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        }
    };
    xhr.send(formData);
});
