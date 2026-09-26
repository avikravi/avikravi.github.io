const MIN_TEMP = 50;
const MAX_TEMP = 90;
const ZONE_LOW = 68;
const ZONE_HIGH = 72;
const SESSION_LENGTH = 60;
const BUTTON_STEP = 1;
const GAUGE_HEIGHT = 300;
const MAX_LEADERBOARD_ENTRIES = 5;

const EVENT_MESSAGES = [
  "Guest arrived!",
  "Storm hit!",
  "Door left open!",
  "AC malfunction!",
];

let currentTemp = 70;
let score = 0;
let overcorrections = 0;
let timeLeft = SESSION_LENGTH;
let gameRunning = false;
let tickIntervalId = null;
let eventTimeoutId = null;

const comfortZoneEl = document.getElementById("comfort-zone");
const needleEl = document.getElementById("temp-needle");
const currentTempEl = document.getElementById("current-temp");
const scoreEl = document.getElementById("score");
const overcorrectionsEl = document.getElementById("overcorrections");
const timeLeftEl = document.getElementById("time-left");
const startBtn = document.getElementById("start-btn");
const statusEl = document.getElementById("status-message");
const leaderboardListEl = document.getElementById("leaderboard-list");

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function tempToPixels(temp) {
  return ((temp - MIN_TEMP) / (MAX_TEMP - MIN_TEMP)) * GAUGE_HEIGHT;
}

function getZoneState(temp) {
  if (temp < ZONE_LOW) return "below";
  if (temp > ZONE_HIGH) return "above";
  return "in";
}

// Temperature gauge
function positionComfortZone() {
  const bottomPx = tempToPixels(ZONE_LOW);
  const topPx = tempToPixels(ZONE_HIGH);
  comfortZoneEl.style.bottom = bottomPx + "px";
  comfortZoneEl.style.height = topPx - bottomPx + "px";
}

function updateGaugeDisplay() {
  needleEl.style.bottom = tempToPixels(currentTemp) + "px";
  currentTempEl.textContent = Math.round(currentTemp) + "°F";
}

// Score and metric display
function updateStatsDisplay() {
  scoreEl.textContent = score;
  overcorrectionsEl.textContent = overcorrections;
  timeLeftEl.textContent = timeLeft;
}

function showStatus(message, durationMs) {
  statusEl.textContent = message;
  if (durationMs) {
    setTimeout(() => {
      if (statusEl.textContent === message) statusEl.textContent = "";
    }, durationMs);
  }
}

function loadLeaderboard() {
  const leaderboard =
    JSON.parse(localStorage.getItem("thermostatPanicLeaderboard")) || [];
  leaderboardListEl.innerHTML = "";
  leaderboard.forEach((entry) => {
    const li = document.createElement("li");
    li.textContent = `${entry.score} pts (${entry.overcorrections} overcorrections)`;
    leaderboardListEl.appendChild(li);
  });
}

function saveScoreToLeaderboard() {
  const leaderboard =
    JSON.parse(localStorage.getItem("thermostatPanicLeaderboard")) || [];
  leaderboard.push({ score: score, overcorrections: overcorrections });
  leaderboard.sort((a, b) => b.score - a.score);
  const trimmed = leaderboard.slice(0, MAX_LEADERBOARD_ENTRIES);
  localStorage.setItem("thermostatPanicLeaderboard", JSON.stringify(trimmed));
  loadLeaderboard();
  return (
    trimmed[0].score === score && trimmed[0].overcorrections === overcorrections
  );
}

function tick() {
  const elapsedFraction = (SESSION_LENGTH - timeLeft) / SESSION_LENGTH;

  const driftMagnitude = 1 + elapsedFraction * 2;
  const direction = Math.random() < 0.5 ? -1 : 1;
  currentTemp = clamp(
    currentTemp + direction * driftMagnitude,
    MIN_TEMP,
    MAX_TEMP,
  );

  if (getZoneState(currentTemp) === "in") {
    score++;
  }

  timeLeft--;
  updateGaugeDisplay();
  updateStatsDisplay();

  if (timeLeft <= 0) {
    endGame();
  }
}

function scheduleNextEvent() {
  const elapsedFraction = (SESSION_LENGTH - timeLeft) / SESSION_LENGTH;
  const maxDelay = 15000 - elapsedFraction * 7000;
  const minDelay = 8000 - elapsedFraction * 4000;
  const delay = minDelay + Math.random() * (maxDelay - minDelay);

  eventTimeoutId = setTimeout(() => {
    if (!gameRunning) return;
    triggerRandomEvent();
    scheduleNextEvent();
  }, delay);
}

function triggerRandomEvent() {
  const message =
    EVENT_MESSAGES[Math.floor(Math.random() * EVENT_MESSAGES.length)];
  const jumpMagnitude = 8 + Math.random() * 7;
  const direction = Math.random() < 0.5 ? -1 : 1;

  currentTemp = clamp(
    currentTemp + direction * jumpMagnitude,
    MIN_TEMP,
    MAX_TEMP,
  );
  updateGaugeDisplay();
  showStatus(message, 2500);
}

// Controls
function adjustTemp(delta) {
  if (!gameRunning) return;

  const prevState = getZoneState(currentTemp);
  currentTemp = clamp(currentTemp + delta, MIN_TEMP, MAX_TEMP);
  const newState = getZoneState(currentTemp);

  const leftZone = prevState === "in" && newState !== "in";
  const skippedZone =
    (prevState === "below" && newState === "above") ||
    (prevState === "above" && newState === "below");
  if (leftZone || skippedZone) {
    overcorrections++;
  }

  updateGaugeDisplay();
  updateStatsDisplay();
}

// Start/status
function startGame() {
  currentTemp = 70;
  score = 0;
  overcorrections = 0;
  timeLeft = SESSION_LENGTH;
  gameRunning = true;

  statusEl.textContent = "";
  startBtn.disabled = true;
  startBtn.textContent = "Playing...";

  updateGaugeDisplay();
  updateStatsDisplay();

  tickIntervalId = setInterval(tick, 1000);
  scheduleNextEvent();
}

function endGame() {
  gameRunning = false;
  clearInterval(tickIntervalId);
  clearTimeout(eventTimeoutId);

  startBtn.disabled = false;
  startBtn.textContent = "Play Again";

  const isNewBest = saveScoreToLeaderboard();
  showStatus(isNewBest ? "Time's up! New best score!" : "Time's up!", null);
}

document
  .getElementById("temp-up")
  .addEventListener("click", () => adjustTemp(BUTTON_STEP));
document
  .getElementById("temp-down")
  .addEventListener("click", () => adjustTemp(-BUTTON_STEP));
startBtn.addEventListener("click", startGame);

positionComfortZone();
updateGaugeDisplay();
updateStatsDisplay();
loadLeaderboard();
