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
        fetch('/api/putclip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                putdata: text
            })
        }).then((response) => {
            return response.json()
        }).then((data) => {
            document.getElementById('share-result').setAttribute('style', 'display: block')
            document.getElementById('share-code').innerText = data.key
        })
    });
});

document.getElementById('copy-button').addEventListener('click', (event) => {
    fetch('/api/getclip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            key: document.getElementById('share-code').innerText
        })
    }).then((response) => {
        return response.json()
    }).then((data) => {
        document.getElementById('copy-result').setAttribute('style', 'display: block');
        navigator.clipboard.writeText(data.data);
    })
});