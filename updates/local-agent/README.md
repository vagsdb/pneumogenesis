# Run the updates agent on your own computer

The updates agent can run on one of your own machines (e.g. the Debian box) instead
of in the cloud. On your machine it has normal internet access (PubMed, journals,
EMA/FDA) and uses your own GitHub login to open pull requests. It follows the same
rules as always: `updates/AGENT.md` on `main`, pull requests only, never merges.

| File | What it is |
|---|---|
| `run.sh` | Runs one agent pass: `run.sh monwed` or `run.sh friday` |
| `prompt-monwed.md`, `prompt-friday.md` | The instructions each run starts from |
| `systemd/` | Timers: Mon & Wed 08:52, Fri 17:47 (Athens time) |

## One-time setup (Debian)

Run these as your normal user (not root) on the machine that will host the agent.

```bash
# 1. Tools (Node.js 18+ must already be installed; NodeSource's nodejs includes npm,
#    so do not also install Debian's separate "npm" package)
sudo apt install -y git gh python3 curl util-linux
mkdir -p ~/.npm-global && npm config set prefix ~/.npm-global   # global npm installs without sudo
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.zshrc     # or ~/.bashrc
export PATH="$HOME/.npm-global/bin:$PATH"
npm install -g @anthropic-ai/claude-code
which claude gh                                                  # both must print a path

# 2. Logins (each opens a browser or shows a code to paste)
claude            # log in to Claude, then type /exit
gh auth login     # GitHub.com → HTTPS → log in with a browser

# 3. A dedicated clone, used only by the agent
git clone https://github.com/vagsdb/pneumogenesis.git ~/pneumogenesis
cd ~/pneumogenesis

# 4. Test once by hand (takes a few minutes; opens a PR if it finds news)
./updates/local-agent/run.sh monwed
```

If the test run works, switch on the schedule:

```bash
mkdir -p ~/.config/systemd/user
cp ~/pneumogenesis/updates/local-agent/systemd/* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now pneumogenesis-agent-monwed.timer pneumogenesis-agent-friday.timer
sudo loginctl enable-linger "$USER"   # keep timers running when you are logged out
systemctl --user list-timers | grep pneumogenesis
```

If you cloned somewhere other than `~/pneumogenesis`, edit `ExecStart=` in
`~/.config/systemd/user/pneumogenesis-agent@.service` before `daemon-reload`.
If `claude` was installed somewhere unusual, add its folder to the `PATH=` line there
(`which claude` shows it).

## Day to day

- **Logs:** `~/.local/state/pneumogenesis-agent/` — one file per run.
- **Run now:** `systemctl --user start pneumogenesis-agent@friday.service`
  (or `@monwed`), or call `run.sh` directly.
- **Pause:** `systemctl --user disable --now pneumogenesis-agent-monwed.timer pneumogenesis-agent-friday.timer`
- **Missed runs:** if the machine was off or asleep at run time, the run happens as
  soon as it is back on (`Persistent=true`).
- **Change the rules:** edit `updates/AGENT.md` on `main` — every run reads it fresh.
  The clone updates itself at the start of each run.

## Safety

- `run.sh` refuses to start if the clone has uncommitted changes, and never runs
  two passes at once.
- The agent's Bash access is limited to `git`, `gh pr`, `curl`, `python3`
  (validator) and a few read-only commands.
- It pushes only `updates/YYYY-MM-DD` branches and opens pull requests; you review
  and merge them on GitHub.

## Only one scheduler

Run the agent from **one** place. If you use this local setup, pause or delete the
cloud routines ("Pneumogenesis updates — …" in claude.ai → Routines), or each run
will open two pull requests.

## On a Mac instead

`run.sh` works on macOS too (install `flock` with `brew install flock`, plus `gh` and
Claude Code). Schedule it with `launchd` or `crontab -e`, e.g.:

```
CRON_TZ=Europe/Athens
52 8 * * 1,3  $HOME/pneumogenesis/updates/local-agent/run.sh monwed
47 17 * * 5   $HOME/pneumogenesis/updates/local-agent/run.sh friday
```

A Mac that sleeps will skip cron runs; the always-on Debian box is the better host.
