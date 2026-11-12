const fps = 25;
let iid = null;

eel.expose(displayError)
function displayError(text) {
    document.querySelector("#error").classList.remove("hidden")
    document.querySelector("#error-box--description").innerHTML = text
}

eel.expose(stopProgram)
function stopProgram() {
    if (iid) {
        clearInterval(iid)
    }
}

eel.expose(displayNewDegree)
function displayNewDegree(deg) {
    document.querySelector("#currDegDisp").value = deg;
    document.querySelector("#currDeg").value = deg;

}

eel.expose(displayClips)
function displayClips(videoPath) {
    const messageContainer = document.querySelector("#list-box");

    // Create the message
    const message = document.createElement('p');
    message.textContent = "Somebody has been caught cheating!";
    message.classList.add('caught-message');

    // Create the button to open the video
    const openButton = document.createElement('button');
    openButton.textContent = "Open Video in File Explorer";
    openButton.classList.add('open-video-button');

    // When the button is clicked, open the video file in the file explorer
    openButton.addEventListener('click', function () {
        eel.openFileExplorer(videoPath);
    });

    // Append the message and button to the container
    messageContainer.appendChild(message);
    messageContainer.appendChild(openButton);

    // Append the container to the body (or any other container you want)
    document.body.appendChild(messageContainer);
}

document.querySelector("#btn--try-again").addEventListener("click", () => {
    eel.start_camera()()
    document.querySelector("#error").classList.add("hidden")
})

document.querySelector("#btn--reconnect").addEventListener("click", () => {
    eel.start_camera()()
    document.querySelector("#live-cam").classList.remove("hidden")
    document.querySelector("#settings").classList.remove("hidden")
    document.querySelector("#btn--reconnect").classList.add("hidden")
})

document.querySelector("#btn--exit").addEventListener("click", () => {
    eel.stop_camera()()
    document.querySelector("#error").classList.add("hidden")
    document.querySelector("#live-cam").classList.add("hidden")
    document.querySelector("#settings").classList.add("hidden")
    document.querySelector("#btn--reconnect").classList.remove("hidden")
})

document.querySelector("#currDeg").addEventListener("change", async () => {
    const currDeg = document.querySelector("#currDeg").value
    document.querySelector("#currDegDisp").value = document.querySelector("#currDeg").value
    await eel.set_camera_deg(Number(currDeg))()
})

document.querySelectorAll('[name="mode"]').forEach(radio => {
    radio.addEventListener("change", () => {
        const selected = document.querySelector('[name="mode"]:checked');
        const currDegEl = document.querySelector("#currDeg")
        if (selected.value == "automatic") {
            currDegEl.disabled = true;
            document.getElementById('live-cam').src = "";
            document.getElementById('cam-info').classList.remove("hidden");
            eel.set_camera_mode("automatic")()
            document.getElementById('cam-info').classList.add("hidden");
        } else {
            currDegEl.disabled = false;
            eel.set_camera_mode("manual")()
        }
    });
});

document.querySelectorAll('[name="recording"]').forEach(radio => {
    radio.addEventListener("change", () => {
        const selected = document.querySelector('[name="recording"]:checked');
        if (selected.value == "rec") {
            eel.set_recording_state(true)()
        } else {
            eel.set_recording_state(false)()
        }
    });
});

function updateFrame() {
    iid = setInterval(async () => {
        const frame = await eel.get_frame()();
        if (frame) document.getElementById('live-cam').src = 'data:image/jpeg;base64,' + frame;
    }, (1/fps) * 1000)
}

eel.start_camera()()
updateFrame();