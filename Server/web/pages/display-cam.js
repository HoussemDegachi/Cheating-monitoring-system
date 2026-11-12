async function updateFrame() {
    const frame = await eel.get_frame()();
    if (frame) document.getElementById('live-cam').src = 'data:image/jpeg;base64,' + frame;
    requestAnimationFrame(updateFrame);
}

eel.start_camera()()
updateFrame();