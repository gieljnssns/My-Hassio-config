// joystick.js
window.onload = function () {
const container = document.createElement('div');
container.innerHTML = `
<h2>🕹️ Robot Joystick</h2>
<canvas id="joystick" width="300" height="300" style="border:1px solid #ccc; touch-action: none;"></canvas>
<p id="joystick-status">Status: ...</p>
`;
document.body.appendChild(container);

const canvas = document.getElementById('joystick');
const ctx = canvas.getContext('2d');
const status = document.getElementById('joystick-status');
const radius = 40;
let dragging = false;

function draw(x, y) {
ctx.clearRect(0, 0, 300, 300);
ctx.beginPath();
ctx.arc(x, y, radius, 0, 2 * Math.PI);
ctx.fillStyle = '#0077cc';
ctx.fill();
}

function normalize(x, y) {
const dx = (x - 150) / 100;
const dy = (150 - y) / 100;
return [Math.max(-1, Math.min(1, dx)), Math.max(-1, Math.min(1, dy))];
}

function motors(x, y) {
let l = y - x;
let r = y + x;
return [Math.max(-1, Math.min(1, l)), Math.max(-1, Math.min(1, r))];
}

function send(left, right) {
fetch('/services/set_motor_speed', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ left_speed: left, right_speed: right })
}).then(() => {
status.textContent = `Links: ${left.toFixed(2)} | Rechts: ${right.toFixed(2)}`;
}).catch(() => {
status.textContent = "Verbindingsfout!";
});
}

function update(x, y) {
draw(x, y);
const [nx, ny] = normalize(x, y);
const [left, right] = motors(nx, ny);
send(left, right);
}

function reset() {
draw(150, 150);
send(0, 0);
}

canvas.addEventListener('mousedown', e => {
dragging = true;
update(e.offsetX, e.offsetY);
});

canvas.addEventListener('mousemove', e => {
if (dragging) update(e.offsetX, e.offsetY);
});

canvas.addEventListener('mouseup', reset);
canvas.addEventListener('mouseleave', reset);

canvas.addEventListener('touchstart', e => {
dragging = true;
const rect = canvas.getBoundingClientRect();
update(e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top);
e.preventDefault();
});

canvas.addEventListener('touchmove', e => {
if (!dragging) return;
const rect = canvas.getBoundingClientRect();
update(e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top);
e.preventDefault();
});

canvas.addEventListener('touchend', () => {
dragging = false;
reset();
});

draw(150, 150);
};