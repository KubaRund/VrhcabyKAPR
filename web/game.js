const byId = (id) => document.getElementById(id);

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

const controls = {
  board: byId("board"), players: byId("players"), dice: byId("dice"),
  turn: byId("turn-title"), turnLabel: byId("turn-label"), status: byId("turn-status"),
  action: byId("main-action"), pause: byId("pause"), hint: byId("hint"),
  moves: byId("moves"), movesPlaceholder: byId("moves-placeholder"),
  history: byId("history"), historyPlaceholder: byId("history-placeholder"),
  error: byId("error"), newGame: byId("new-game"), setup: byId("setup"),
  setupForm: byId("setup-form"), setupError: byId("setup-error"), rules: byId("rules"),
};

const moveLabels = { KILL: "vyhození", SAVE: "zajištění", END: "vynesení", MOVE: "přesun" };
const pips = [[], [4], [0, 8], [0, 4, 8], [0, 2, 6, 8], [0, 2, 4, 6, 8], [0, 2, 3, 5, 6, 8]];
const slots = new Map();
let state;
let busy = false;
let paused = false;
let chosen = null;
let hinted = null;
let message = "";
let computerTimer;

function checker(white) {
  const node = element("span", `checker ${white ? "ivory" : "dark"}`);
  node.setAttribute("aria-hidden", "true");
  return node;
}

function buildSpot(position, row, column, special = "") {
  const className = special ? `spot special ${special}` : `spot point ${column % 2 ? "light" : ""}`;
  const button = element("button", `${className} ${row === 1 ? "top" : "bottom"}`);
  button.type = "button";
  button.style.gridRow = row;
  button.style.gridColumn = column;
  const number = element("span", "point-number", special ? (special === "off" ? "Ven" : "Bar") : position + 1);
  const tokens = element("span", "tokens");
  button.append(number, tokens);
  button.addEventListener("click", () => selectPoint(position));
  controls.board.append(button);
  slots.set(position, { button, tokens });
}

function buildBoard() {
  controls.board.append(element("div", "bar-rail"));
  for (let index = 0; index < 12; index += 1) {
    const column = index + (index < 6 ? 1 : 2);
    buildSpot(11 - index, 1, column);
    buildSpot(12 + index, 2, column);
  }
  buildSpot(24, 1, 7, "bar");
  buildSpot(25, 2, 7, "bar");
  buildSpot(27, 1, 14, "off");
  buildSpot(26, 2, 14, "off");
}

function spotName(position) {
  if (position < 24) return `bod ${position + 1}`;
  if (position < 26) return position === 24 ? "bar bílých" : "bar černých";
  return position === 26 ? "vynesené kameny bílých" : "vynesené kameny černých";
}

function compactPoint(position) {
  if (position < 24) return position + 1;
  return position < 26 ? "bar" : "ven";
}

function humanTurn() {
  return state?.players.length && state.winner === null && !state.players[state.turn].computer;
}

function renderBoard() {
  const last = state?.lastMove;
  const moves = humanTurn() ? state.moves : [];
  const sources = new Set(moves.map(([source]) => source));
  const targets = new Set(moves.filter(([source]) => source === chosen).map(([, target]) => target));
  for (const [position, { button, tokens }] of slots) {
    const amount = state?.points[position] ?? 0;
    const count = Math.abs(amount);
    const pieces = Array.from({ length: Math.min(position >= 24 ? 3 : 4, count) }, () => checker(amount > 0));
    if (count > pieces.length) pieces.push(element("span", "stack-count", count));
    tokens.replaceChildren(...pieces);
    button.classList.toggle("source", sources.has(position));
    button.classList.toggle("target", targets.has(position));
    button.classList.toggle("selected", position === chosen);
    button.classList.toggle("last", last?.slice(0, 2).includes(position) ?? false);
    const action = targets.has(position) ? ", cíl tahu" : sources.has(position) ? ", lze vybrat" : "";
    const piecesLabel = count ? `, ${count} ${amount > 0 ? "bílých" : "černých"}` : ", prázdné";
    const selectable = !busy && (sources.has(position) || targets.has(position));
    button.tabIndex = selectable ? 0 : -1;
    button.setAttribute("aria-disabled", String(!selectable));
    button.setAttribute("aria-label", spotName(position) + piecesLabel + action);
    if (sources.has(position)) button.setAttribute("aria-pressed", String(position === chosen));
    else button.removeAttribute("aria-pressed");
  }
}

function renderPlayers() {
  const players = state?.players.length ? state.players : [
    { name: "Bílý", color: "W" }, { name: "Černý", color: "K" },
  ];
  controls.players.replaceChildren(...players.map((player, index) => {
    const active = state?.players.length && state.winner === null && state.turn === index;
    const row = element("div", `player${active ? " active" : ""}`);
    const title = element("div", "player-title");
    title.append(element("strong", "", player.name));
    if (player.pips !== undefined) title.append(element("small", "", `${player.computer ? "Počítač" : "Člověk"} · ${player.off}/15 venku`));
    row.append(checker(player.color === "W"), title);
    if (player.pips !== undefined) {
      const stats = element("div", "player-stats");
      stats.title = "Součet kroků do vynesení všech kamenů";
      stats.append(element("strong", "", player.pips), element("small", "", "kroků"));
      row.append(stats);
    }
    return row;
  }));
}

function renderDice() {
  const dice = state?.rolls?.length ? state.rolls : [null, null];
  controls.dice.replaceChildren(...dice.map((value) => {
    const face = element("span", `die${value === null ? " waiting" : ""}`);
    face.setAttribute("role", "img");
    face.setAttribute("aria-label", value === null ? "Čeká na hod" : `Kostka ${value}`);
    if (value !== null) {
      for (const position of pips[value]) {
        const dot = element("span", "pip");
        dot.style.gridRow = Math.floor(position / 3) + 1;
        dot.style.gridColumn = position % 3 + 1;
        face.append(dot);
      }
    }
    return face;
  }));
}

function renderTurn() {
  const player = state?.players[state.turn];
  const winner = state?.players[state.winner];
  controls.pause.hidden = !player?.computer || Boolean(winner);
  controls.pause.textContent = paused ? "Pokračovat" : "Pozastavit";
  controls.action.hidden = Boolean(player?.computer && !paused && !winner);
  controls.action.disabled = busy;
  if (!state) {
    controls.turnLabel.textContent = "Partie";
    controls.turn.textContent = "Vrhcáby";
    controls.status.textContent = busy ? "Otevírám partii…" : "Partii se nepodařilo načíst.";
    controls.action.textContent = "Zkusit znovu";
  } else if (winner) {
    controls.turnLabel.textContent = "Konec partie";
    controls.turn.textContent = `Vyhrál ${winner.name}`;
    controls.status.textContent = `Výsledek: ${state.result}.`;
    controls.action.textContent = "Nová partie";
  } else if (!player) {
    controls.turnLabel.textContent = "Partie";
    controls.turn.textContent = "Vrhcáby pro dva";
    controls.status.textContent = "Vyber dva hráče nebo si zahraj proti počítači.";
    controls.action.textContent = "Rozehrát partii";
  } else {
    controls.turnLabel.textContent = state.opening ? "Zahájení" : "Na tahu";
    controls.turn.textContent = player.name;
    if (player.computer) {
      controls.status.textContent = paused ? "Počítač je pozastavený." : "Počítač hraje svůj tah.";
      controls.action.textContent = "Další krok";
    } else if (state.rolls === null) {
      controls.status.textContent = state.opening ? "Vyšší zahajovací hod určí začínajícího hráče." : "Hoď kostkami a vyber tah.";
      controls.action.textContent = state.opening ? "Zobrazit zahajovací hod" : "Hodit kostkami";
    } else if (!state.moves.length) {
      controls.status.textContent = state.rolls.length ? "Žádný z dostupných přesunů není možný." : "Všechny kostky jsou odehrané.";
      controls.action.textContent = "Předat tah";
    } else {
      controls.status.textContent = message || (chosen === null ? "Vyber kámen nebo tah v seznamu." : "Vyber zvýrazněný cíl.");
      controls.action.hidden = true;
    }
  }
}

function renderMoves() {
  const available = humanTurn() ? state.moves.map((move, index) => ({ move, index })) : [];
  const shown = chosen === null ? available : available.filter(({ move }) => move[0] === chosen);
  controls.movesPlaceholder.hidden = shown.length > 0;
  controls.movesPlaceholder.textContent = state?.winner !== null && state?.winner !== undefined
    ? "Partie skončila."
    : "Až budeš na tahu a hodíš kostkami, zobrazí se dostupné přesuny.";
  controls.hint.hidden = !available.length;
  controls.hint.disabled = busy;
  controls.moves.replaceChildren(...shown.map(({ move: [source, target, die, kind], index }) => {
    const button = element("button", `entry-button${hinted === index ? " suggested" : ""}`);
    button.type = "button";
    button.disabled = busy;
    button.append(
      element("span", "", `${compactPoint(source)} → ${compactPoint(target)} · ${moveLabels[kind]}`),
      element("span", "move-die", die),
    );
    button.setAttribute("aria-label", `${spotName(source)} na ${spotName(target)}, kostka ${die}, ${moveLabels[kind]}`);
    button.addEventListener("click", () => change("move", { move: index }));
    const row = element("li", "");
    row.append(button);
    return row;
  }));
  controls.historyPlaceholder.hidden = Boolean(state?.history.length);
  controls.history.replaceChildren(...(state?.history ?? []).map(([player, move]) => element("li", "", `${player}: ${move}`)));
}

function render() {
  renderBoard();
  renderPlayers();
  renderDice();
  renderTurn();
  renderMoves();
  controls.newGame.disabled = busy || !state;
}

function setError(text) {
  const target = controls.setup.open ? controls.setupError : controls.error;
  target.hidden = !text;
  target.textContent = text;
}

function setState(updated) {
  state = updated;
  chosen = null;
  hinted = null;
  message = "";
  setError(updated.loadError ?? "");
}

function scheduleComputer() {
  clearTimeout(computerTimer);
  if (!busy && !paused && !controls.setup.open && !controls.rules.open
      && state?.winner === null && state.players[state.turn]?.computer) {
    computerTimer = setTimeout(() => change("computer"), 450);
  }
}

async function load() {
  busy = true;
  render();
  try {
    const response = await fetch("/api/game", { cache: "no-store" });
    if (!response.ok) throw Error("Odpověď hry se nepodařilo načíst.");
    setState(await response.json());
  } catch (error) {
    setError(error.message);
  } finally {
    busy = false;
    render();
    scheduleComputer();
  }
}

async function change(action, extra = {}) {
  if (busy || !state) return;
  busy = true;
  render();
  try {
    const response = await fetch("/api/game", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, revision: state.revision, ...extra }),
    });
    const updated = await response.json();
    if (updated.revision !== undefined) setState(updated);
    if (response.status === 409) {
      setError("Partie mezitím pokračovala v jiné kartě. Zobrazila se aktuální pozice.");
    } else if (!response.ok) {
      throw Error(updated.error ?? "Krok se nepodařilo provést.");
    } else if (action === "new") {
      paused = false;
      controls.setup.close();
      setError("");
    }
  } catch (error) {
    if (action === "computer") paused = true;
    setError(error.message);
  } finally {
    busy = false;
    render();
    scheduleComputer();
  }
}

function selectPoint(position) {
  if (busy || !humanTurn()) return;
  const candidates = state.moves.map((move, index) => ({ move, index }));
  if (chosen === position) {
    chosen = null;
  } else {
    const matches = candidates.filter(({ move: [from, to] }) => chosen === from && position === to);
    if (matches.length === 1) {
      change("move", { move: matches[0].index });
      return;
    }
    if (matches.length > 1) {
      message = "Na tento bod vedou dvě kostky. Vyber kostku v seznamu tahů.";
      renderTurn();
      controls.moves.querySelector("button")?.focus();
      return;
    }
    if (!candidates.some(({ move }) => move[0] === position)) return;
    chosen = position;
  }
  message = "";
  hinted = null;
  render();
}

function openSetup() {
  if (busy || !state) return;
  clearTimeout(computerTimer);
  byId("replace-note").hidden = !state.hasSave;
  controls.setup.showModal();
  setError("");
}

controls.action.addEventListener("click", () => {
  if (!state) return load();
  const player = state.players[state.turn];
  if (!player || state.winner !== null) return openSetup();
  if (player.computer) return change("computer");
  if (state.rolls === null) return change("roll");
  if (!state.moves.length) return change("pass");
});
controls.pause.addEventListener("click", () => {
  paused = !paused;
  render();
  scheduleComputer();
});
controls.hint.addEventListener("click", () => {
  if (!humanTurn() || state.hint === null) return;
  hinted = state.hint;
  chosen = state.moves[hinted][0];
  message = "Doporučený tah je označený v seznamu.";
  render();
});
controls.setupForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(controls.setupForm);
  const players = ["white", "black"].map((color) => ({ name: form.get(`${color}-name`), kind: form.get(`${color}-kind`) }));
  change("new", { players });
});
controls.newGame.addEventListener("click", openSetup);
byId("cancel-setup").addEventListener("click", () => controls.setup.close());
byId("how-to").addEventListener("click", () => {
  controls.rules.showModal();
  scheduleComputer();
});
controls.setup.addEventListener("close", scheduleComputer);
controls.rules.addEventListener("close", scheduleComputer);

buildBoard();
load();
