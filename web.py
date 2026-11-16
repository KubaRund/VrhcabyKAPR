import argparse
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

from board import BAR, OFF, Board
from main import COMPUTER, HUMAN, Game
from player import Player
from progress import DEFAULT_SAVE, format_entry


ASSETS = Path(__file__).with_name("web")
ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/game.js": ("game.js", "text/javascript; charset=utf-8"),
}


class GameSession:
    def __init__(self, save_path):
        self.save_path = save_path
        self.revision = 0
        self.lock = Lock()
        self.restore()

    def restore(self):
        self.game = Game(Board(), self.save_path)
        self.load_error = None
        try:
            self.game.load_game()
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
            self.load_error = f"Uloženou partii se nepodařilo otevřít. {error}"

    def snapshot(self):
        game = self.game
        options = game.legal_options() if game.players else []
        current = game.players[game.next_player] if game.players else None
        winner = game.winner()
        return {
            "revision": self.revision,
            "points": game.board.position(),
            "players": [
                {
                    "name": player.name, "color": player.color, "computer": player.type == COMPUTER,
                    "pips": game.board.pips(player.color),
                    "bar": len(game.board.stacks[BAR[player.color]].stack),
                    "off": len(game.board.stacks[OFF[player.color]].stack),
                }
                for player in game.players
            ],
            "turn": game.next_player,
            "opening": bool(game.opening_rolls),
            "rolls": None if game.remaining_rolls is None else game.remaining_rolls.copy(),
            "moves": options,
            "hint": current.choose_option(options, game.board) - 1 if options else None,
            "winner": game.players.index(winner) if winner else None,
            "result": game.win_type(winner) if winner else None,
            "history": [format_entry(entry) for entry in reversed(game.progress[-10:])],
            "lastMove": game.progress[-1]["move"] if game.progress and isinstance(game.progress[-1], dict) else None,
            "hasSave": self.save_path.is_file(),
            "loadError": self.load_error,
        }

    def start_game(self, rows):
        if not isinstance(rows, list) or len(rows) != 2:
            raise ValueError("Vyber dva hráče.")
        players = []
        for row, color, default_name in zip(rows, ("W", "K"), ("Bílý", "Černý")):
            if not isinstance(row, dict) or not isinstance(row.get("name"), str):
                raise ValueError("Zadej jméno hráče.")
            kind = row.get("kind")
            name = row["name"].strip() or default_name
            if kind not in ("human", "computer") or len(name) > 32:
                raise ValueError("Hráč potřebuje platný typ a jméno do 32 znaků.")
            players.append(Player(COMPUTER if kind == "computer" else HUMAN, name, color))
        self.game.begin(players)
        self.load_error = None

    def dispatch(self, payload):
        if not isinstance(payload, dict) or type(payload.get("revision")) is not int:
            raise ValueError("Neplatný požadavek na změnu partie.")
        if payload["revision"] != self.revision:
            return 409

        action = payload.get("action")
        game = self.game
        try:
            if action == "new":
                self.start_game(payload.get("players"))
            else:
                if not game.players or game.winner():
                    raise ValueError("Nejdřív založ novou partii.")
                player = game.players[game.next_player]
                options = game.legal_options()
                self.play_action(action, payload.get("move"), player, options)
        except OSError:
            self.restore()
            self.revision += 1
            raise
        self.revision += 1
        return 200

    def play_action(self, action, index, player, options):
        game = self.game
        if action == "computer" and player.type == COMPUTER:
            if game.remaining_rolls is None:
                game.roll_turn()
            elif options:
                game.play_move(options[player.choose_option(options, game.board) - 1])
            else:
                game.finish_turn()
        elif action == "roll" and player.type == HUMAN and game.remaining_rolls is None:
            game.roll_turn()
        elif action == "move" and player.type == HUMAN and type(index) is int and 0 <= index < len(options):
            game.play_move(options[index])
        elif action == "pass" and player.type == HUMAN and game.remaining_rolls is not None and not options:
            game.finish_turn()
        else:
            raise ValueError("Tento krok teď nelze provést.")


class Handler(BaseHTTPRequestHandler):
    def send_body(self, status, mime, body):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        self.send_body(status, "application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False).encode())

    def is_local(self):
        port = self.server.server_address[1]
        hosts = (f"127.0.0.1:{port}", f"localhost:{port}")
        host = self.headers.get("Host")
        return host in hosts and self.headers.get("Origin") in (None, f"http://{host}")

    def do_GET(self):
        if not self.is_local():
            self.send_error(403)
        elif self.path == "/api/game":
            with self.server.session.lock:
                snapshot = self.server.session.snapshot()
            self.send_json(200, snapshot)
        elif self.path in ROUTES:
            name, mime = ROUTES[self.path]
            self.send_body(200, mime, (ASSETS / name).read_bytes())
        else:
            self.send_error(404)

    def do_POST(self):
        if not self.is_local():
            self.send_error(403)
            return
        if self.path != "/api/game":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if self.headers.get_content_type() != "application/json" or not 1 <= size <= 8192:
                raise ValueError("Neplatný požadavek.")
            request = json.loads(self.rfile.read(size))
        except ValueError:
            self.send_json(400, {"error": "Neplatný požadavek."})
            return

        session = self.server.session
        with session.lock:
            try:
                status = session.dispatch(request)
                answer = session.snapshot()
            except ValueError as error:
                status, answer = 400, {"error": str(error)}
            except OSError as error:
                status = 503
                answer = {**session.snapshot(), "error": f"Partii se nepodařilo uložit. {error}"}
        self.send_json(status, answer)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Grafické vrhcáby v prohlížeči.")
    parser.add_argument("--uloha", type=Path, default=DEFAULT_SAVE, help="cesta k uložené partii")
    parser.add_argument("--port", type=int, default=8765, help="místní port aplikace")
    parser.add_argument("--bez-prohlizece", action="store_true", help="neotevírá prohlížeč automaticky")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("Port musí být od 0 do 65535.")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as error:
        parser.error(str(error))
    with server:
        server.session = GameSession(args.uloha)
        url = f"http://127.0.0.1:{server.server_address[1]}"
        print(f"Vrhcáby běží na {url}", flush=True)
        if not args.bez_prohlizece:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
