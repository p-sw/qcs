function tab_switch(tab_id) {
    Array.prototype.forEach.call(document.getElementsByClassName('tab-btn'), (el) => {
        if (el.id == tab_id) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    })
    Array.prototype.forEach.call(document.getElementsByClassName('tab-content'), (el) => {
        if (el.id == document.getElementById(tab_id).getAttribute('name')) {
            el.setAttribute('style', 'display:block');
        } else {
            el.setAttribute('style', 'display:none');
        }
    })
}

Array.prototype.forEach.call(document.getElementsByClassName('tab-btn'), (el) => {
    el.addEventListener('click', (event) => {
        tab_switch(event.target.id)
    });
});

document.getElementById('share-button').addEventListener('click', (event) => {
    navigator.clipboard.readText().then((text) => {
        if (document.getElementById('use-custom-encrypt').checked) {
            var datatxt = CryptoJS.AES.encrypt(text, document.getElementById('encrypt-pass').value).toString();
        } else {
            var datatxt = text;
        }
        let bodydata = {
            putdata: datatxt,
            encrypt: document.getElementById('use-custom-encrypt').checked
        }
        fetch('/api/putclip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(bodydata)
        }).then((response) => {
            return response.json()
        }).then((data) => {
            document.getElementById('share-result').setAttribute('style', 'display: block')
            document.getElementById('share-code').innerText = data.key
        })
    });
});

function make_result_visible(result_type) {
    Array.prototype.forEach.call(document.getElementById("copy-result").getElementsByTagName('div'), (el) => {
        if (el.id == result_type) {
            el.setAttribute('style', 'display:block');
        } else {
            el.setAttribute('style', 'display:none');
        }    
    })
}

document.getElementById('copy-button').addEventListener('click', (event) => {
    fetch('/api/getclip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            key: document.getElementById('copy-code').value
        })
    }).then((response) => {
        return response.json()
    }).then((data) => {
        if(Object.keys(data).includes('error')) {  // error
            make_result_visible('copy-result-error-code');
        } else { // success
            if (data.encrypted) { // encrypted
                document.getElementById('decrypt-pass-container').setAttribute('style', 'display: block;')
                document.getElementById('temp-not-decrypted').value = data.data
                document.getElementById('copy-code').setAttribute('disabled', 'disabled')
                document.getElementById('copy-button').setAttribute('disabled', 'disabled')
            } else { // not encrypted
                document.getElementById('copy-result').setAttribute('style', 'display: block');
                make_result_visible('copy-result-success');
                navigator.clipboard.writeText(data.data);
            }
        }
    })
});

document.getElementById('decrypt-button').addEventListener('click', (event) => {
    var text_not_decrypted = document.getElementById('temp-not-decrypted').value;
    var password = document.getElementById('decrypt-pass').value;
    try {
        var text_decrypted = CryptoJS.AES.decrypt(text_not_decrypted, password).toString(CryptoJS.enc.Utf8);
    } catch (error) {
        make_result_visible('decrypt-result-error-pass');
        return;
    }
    document.getElementById('copy-result').setAttribute('style', 'display: block');
    if (text_decrypted) {
        navigator.clipboard.writeText(text_decrypted);
        make_result_visible('copy-result-success');
    } else {
        make_result_visible('copy-result-error-pass');
    }
    document.getElementById('decrypt-pass-container').setAttribute('style', 'display: none;')
    document.getElementById('temp-not-decrypted').value = ''
    document.getElementById('copy-code').removeAttribute('disabled')
    document.getElementById('copy-button').removeAttribute('disabled')
});