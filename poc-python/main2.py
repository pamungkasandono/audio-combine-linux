import curses
import subprocess
import re


class AudioCombineTUI:

    def __init__(self):
        self.selected = set()
        self.cursor = 0
        self.message = "Ready"

        self.supported = self.check_support()

        if self.supported:
            self.sinks = self.get_sinks()
            self.load_existing_combined()
        else:
            self.sinks = []

    def get_sinks(self):
        result = subprocess.check_output(
            ["pactl", "list", "short", "sinks"],
            text=True
        )

        sinks = []

        for line in result.strip().split("\n"):
            parts = re.split(r"\s+", line)

            if len(parts) >= 2:
                sink_name = parts[1]

                if sink_name.startswith("Combined"):
                    continue

                label = sink_name

                if "Speaker" in sink_name:
                    label = "Laptop Speaker"

                elif "HDMI1" in sink_name:
                    label = "HDMI Output 1"

                elif "HDMI2" in sink_name:
                    label = "HDMI Output 2"

                elif "HDMI3" in sink_name:
                    label = "HDMI Output 3"

                elif sink_name.startswith("bluez_output"):
                    try:
                        desc_output = subprocess.check_output(
                            ["pactl", "list", "sinks"],
                            text=True
                        )

                        blocks = desc_output.split("Sink #")

                        for block in blocks:
                            if sink_name in block:
                                match = re.search(
                                    r'device.description = "(.*?)"',
                                    block
                                )

                                if match:
                                    label = f"Bluetooth: {match.group(1)}"

                                break

                    except Exception:
                        pass

                sinks.append({
                    "name": sink_name,
                    "label": label
                })

        return sinks

    def remove_combined_sinks(self):
        modules = subprocess.check_output(
            ["pactl", "list", "short", "modules"],
            text=True
        )

        for line in modules.strip().split("\n"):
            if "module-combine-sink" in line:
                module_id = line.split()[0]

                subprocess.run([
                    "pactl",
                    "unload-module",
                    module_id
                ])

    def move_audio_streams(self):
        try:
            result = subprocess.check_output(
                ["pactl", "list", "short", "sink-inputs"],
                text=True
            )

            for line in result.strip().split("\n"):
                if not line.strip():
                    continue

                input_id = line.split()[0]

                subprocess.run([
                    "pactl",
                    "move-sink-input",
                    input_id,
                    combined_name
                ])

        except Exception:
            pass

    def combine_selected(self):
        selected_names = [
            sink["name"]
            for idx, sink in enumerate(self.sinks)
            if idx in self.selected
        ]

        selected_labels = [
            sink["label"]
            for idx, sink in enumerate(self.sinks)
            if idx in self.selected
        ]

        if len(selected_names) == 0:
            self.remove_combined_sinks()
            self.message = "All combined sinks removed"
            return

        if len(selected_names) == 1:
            self.message = "Select at least 2 outputs"
            return

        self.remove_combined_sinks()

        slaves = ",".join(selected_names)

        combined_name = "Combined:" + "_".join(
            label
                .replace(" ", "")
                .replace(":", "")
                .replace("+", "")
            for label in selected_labels
        )

        subprocess.run([
            "pactl",
            "load-module",
            "module-combine-sink",
            f"sink_name={combined_name}",
            f"slaves={slaves}"
        ])

        subprocess.run([
            "pactl",
            "set-default-sink",
            combined_name
        ])

        self.move_audio_streams()
        self.message = (
            "Combined: " +
            " + ".join(selected_labels)
        )

    def draw(self, stdscr):
        stdscr.clear()

        stdscr.addstr(0, 0, "Select audio outputs to combine:\n")

        for idx, sink in enumerate(self.sinks):

            prefix = "[x]" if idx in self.selected else "[ ]"

            line = f"{prefix} {sink['label']}"

            if idx == self.cursor:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, line)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, line)

        footer_y = len(self.sinks) + 4

        stdscr.addstr(
            footer_y,
            0,
            "SPACE = toggle | ENTER = combine | R = refresh | DEL = remove combined | Q = quit"
        )

        stdscr.addstr(
            footer_y + 2,
            0,
            f"[INFO] {self.message}"
        )

        stdscr.refresh()


    def load_existing_combined(self):
        try:
            modules = subprocess.check_output(
                ["pactl", "list", "short", "modules"],
                text=True
            )

            for line in modules.strip().split("\n"):

                if "module-combine-sink" not in line:
                    continue

                match = re.search(
                    r"slaves=([^ ]+)",
                    line
                )

                if not match:
                    continue

                slaves = match.group(1).split(",")

                for idx, sink in enumerate(self.sinks):

                    if sink["name"] in slaves:
                        self.selected.add(idx)

        except Exception:
            pass

    def refresh_sinks(self):
        old_selected_names = {
            self.sinks[idx]["name"]
            for idx in self.selected
            if idx < len(self.sinks)
        }

        self.sinks = self.get_sinks()

        self.selected.clear()

        for idx, sink in enumerate(self.sinks):

            if sink["name"] in old_selected_names:
                self.selected.add(idx)

        self.cursor = min(
            self.cursor,
            len(self.sinks) - 1
        )

        self.message = "Device list refreshed"

    def check_support(self):
        try:
            subprocess.check_output(
                ["which", "pactl"],
                text=True
            )

        except Exception:

            self.message = (
                "Audio combine is not supported on this system | "
                "Missing dependency: pactl | "
                "Check: which pactl"
            )

            return False

        try:
            subprocess.check_output(
                ["pactl", "info"],
                text=True
            )

        except Exception:

            self.message = (
                "Audio combine requires PulseAudio/PipeWire | "
                "Audio server unavailable | "
                "Check: pactl info"
            )

            return False

        return True

    def run(self, stdscr):

        curses.curs_set(0)

        while True:

            self.draw(stdscr)

            key = stdscr.getch()

            if key == curses.KEY_UP:
                self.cursor = max(0, self.cursor - 1)

            elif key == curses.KEY_DOWN:
                self.cursor = min(
                    len(self.sinks) - 1,
                    self.cursor + 1
                )

            elif key == ord(" "):

                if self.cursor in self.selected:
                    self.selected.remove(self.cursor)
                else:
                    self.selected.add(self.cursor)

            elif key == curses.KEY_ENTER or key in [10, 13]:
                self.combine_selected()

            elif key == curses.KEY_DC:
                self.remove_combined_sinks()
                self.selected.clear()
                self.message = "Combined sink removed"

            elif key == ord("q"):
                break

            elif key == ord("r"):
                self.refresh_sinks()


if __name__ == "__main__":

    app = AudioCombineTUI()

    if not app.supported:

        print()
        print(f"[ERROR] {app.message}")
        print()

        exit(1)

    curses.wrapper(app.run)