const clientURL = '/d/api/admin/client/'
const screenURL = '/d/api/admin/screen/'
const reloadQRURL= '/d/api/admin/screen/reload'
const infoURL = '/d/api/admin/current'
const newAdminURL= '/d/api/admin/users/'

const spinner = '<div class="fas fa-sync fa-spin"></div>'


// Validate form inputs as non-empty strings
const validate = (obj) => !Object.values(obj).some(x => (x === ''));

// Convert form to key, value pair
const serializeForm = function (form) {
	return Object.fromEntries(new FormData(form));
};

const parseForm = (formID) => {
  var fd = document.getElementById(formID);
  var sForm = serializeForm(fd);
  return sForm
}

// Disable or enable button during processing
const disableBtn = (btnID, enable=false, text="") => {
  var btn = document.getElementById(btnID);
  var action = enable ? false : true
  btn.disabled = action;
  if (text) {
    btn.innerHTML = text;
  }
}

// Shou notification messages
const displayMessage = (message, alertType="success") => {
  // success, warn, danger
  var header = document.getElementById("header")
  var newDiv = document.createElement('div')
  newDiv.className = `c_alert ${alertType} user-menu-toggle text-center`
  newDiv.innerHTML = message

  header.appendChild(newDiv)

  setTimeout(function(){
    if (header.firstElementChild) {
      header.removeChild(header.childNodes[1]);
    }
  }, 8000)

}


// Add a new admin user
document.getElementById("add-admin-user-btn").addEventListener(
  "click", addAdminUser, false
);

async function addAdminUser() {
  try {
    var sForm = parseForm ('add_new_admin')
    var isValidForm = validate(sForm);

    if (!isValidForm) return
    disableBtn('add-admin-user-btn', enable=false, text=spinner)

    fetch(newAdminURL, {
      method: 'post',
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(sForm)
    })
    .then(res => res.json())
    .then(res => {

      displayMessage(`Admin user "${sForm.username}" created.`, "info");
      disableBtn('add-admin-user-btn', enable=true, text="Add");

    })
  } catch (err) {
    displayMessage(`An error occured: ${err}.`, "danger");
    console.error(`An error occured: ${err}.`);
  }
}

// Add a new client
document.getElementById("add-client-btn").addEventListener(
  "click", addClient, false
);

async function addClient() {
  try {

    var sForm = parseForm ('add_new_client')
    var isValidForm = validate(sForm);

    if (!isValidForm) return;

    disableBtn('add-client-btn', enable=false, text=spinner);

    var message = `Setting up driver for client "${sForm.clientID}". This might take a minute.`
    displayMessage(message, "info")

    fetch(clientURL, {
      method: 'post',
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(sForm)
    }
  )
  .then(res => res.json())
  .then(
    res => {
      disableBtn('add-client-btn', enable=true, text='Add')
      disableBtn('qr-modal-button', enable=true)
      displayMessage(`QR Code for "${sForm.clientID}" is available.`)
      updateUI()
    }
  )
  } catch (err) {
    displayMessage(`An error occured: ${err}.`, "danger")
    console.error(`An error occured: ${err}.`);
  }
}


// Delete a client
document.getElementById("delete-client-btn").addEventListener(
  "click", deleteClient, false
);

async function deleteClient() {
  var sForm = parseForm ('delete_client')
  var isValidForm = validate(sForm);

  if (!isValidForm) return

  var clientID = sForm.clientID
  disableBtn('delete-client-btn', enable=false, text=spinner)

  fetch(clientURL + clientID, {
    method: 'DELETE',
  })
  .then(res => res.json())
  .then(res => {
    if (res.error) {
      displayMessage(res.error, "danger")
    } else {
      var msg = `Client "${res.client_id}" deleted successfully.`
      displayMessage(msg, "success")
    }
    disableBtn('delete-client-btn', enable=true, text='Delete')
    updateUI()
  }

  )
}


// reload qr image
document.getElementById("reload-qr").addEventListener(
  "click", deleteClient, false
);

function reloadQR() {
  fetch(reloadQRURL + clientID, {
    method: 'GET',
  })
  .then(res => res.arrayBuffer())
  .then(buffer => {
    var base64Flag = 'data:image/jpeg;base64,';
    var imageStr = arrayBufferToBase64(buffer);

    document.getElementById("modal-img").src = base64Flag + imageStr;
  })
}


$(function(){
    $("#qr-modal-button").click(function() {

      var sForm = parseForm ('add_new_client')
      var isValidForm = validate(sForm);

      if (!isValidForm) return

      fetch(screenURL + sForm.clientID, {
        method: 'GET'
      })
      .then(res => res.arrayBuffer())
      .then(buffer => {
        var base64Flag = 'data:image/jpeg;base64,';
        var imageStr = arrayBufferToBase64(buffer);

        document.getElementById("modal-img").src = base64Flag + imageStr;

      })

    $("#myModal").modal('toggle');
  });
});


function arrayBufferToBase64(buffer) {
  var binary = '';
  var bytes = [].slice.call(new Uint8Array(buffer));

  bytes.forEach((b) => binary += String.fromCharCode(b));

  return window.btoa(binary);
};

// Pull new data from backend and update UI.
const updateUIInfo = (info) => {
  var total_clients = document.getElementById("total_clients")
  var no_active_clients = document.getElementById("no_active_clients")
  var no_inactive_clients = document.getElementById("no_inactive_clients")
  var clients_info_table = document.getElementById("clients_info_table")

  total_clients.innerHTML = info.total_clients
  no_active_clients.innerHTML = info.no_active_clients
  no_inactive_clients.innerHTML = info.no_inactive_clients

  // clear previous data
  clients_info_table.innerHTML = "";

  info.clients_info.forEach((client, index) => {
    var row = document.createElement("tr");
    var thd = document.createElement("th");
    var col1= document.createElement("td");
    var col2= document.createElement("td");
    var col3= document.createElement("td");
    var col4= document.createElement("td");

    // addendum
    thd.scope = "row";

    // add text
    thd.textContent = index + 1;
    col1.textContent = client.client_id;
    col2.innerHTML += '<p class="td-wrap-long">' + client.driver_status + '</p>';
    col3.textContent = client.service_url;
    col4.textContent = client.created_at;

    // add to parent
    clients_info_table.appendChild(thd);
    clients_info_table.appendChild(col1);
    clients_info_table.appendChild(col2);
    clients_info_table.appendChild(col3);
    clients_info_table.appendChild(col4);
    clients_info_table.appendChild(row);
  });
}


const updateUI = () => {
  fetch(infoURL, {
    method: 'GET'
  })
  .then(res => res.json())
  .then(info => {
    updateUIInfo(info)
  })
}

updateUI()
