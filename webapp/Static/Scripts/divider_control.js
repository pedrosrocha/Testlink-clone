const divider = document.getElementById('divider');
let isResizing = false;

divider.addEventListener('mousedown', (e) => {
    isResizing = true;
    document.body.style.cursor = 'col-resize';
});

document.addEventListener('mousemove', (e) => {
    const leftColumn = document.getElementById('left-column');

    if (!isResizing) return;

    const newWidth = e.clientX;

    leftColumn.style.width = newWidth + 'px';
});

document.addEventListener('mouseup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});
