import subprocess
import re
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Checkbox, Button, Static
from textual.containers import VerticalScroll


class AudioCombineApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #container {
        width: 80%;
        height: 90%;
        border: solid green;
        padding: 1;
    }

    Button {
        margin-top: 1;
    }
    """

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

                if sink_name.startswith("combined"):
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

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll(id="container"):
            yield Static("Select audio outputs to combine:\n")

            self.sinks = self.get_sinks()

            for sink in self.sinks:
                sink_name = sink["name"]
                sink_label = sink["label"]
                safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", sink_name)
                yield Checkbox(sink_label, id=safe_id)

            yield Button("Create Combined Sink", id="create")
            yield Button("Remove Combined Sink", id="remove")

            self.status = Static("")
            yield self.status

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create":
            selected = []

            for sink in self.sinks:
                sink_name = sink["name"]

                safe_id = re.sub(
                    r"[^a-zA-Z0-9_-]",
                    "_",
                    sink_name
                )

                checkbox = self.query_one(
                    f"#{safe_id}",
                    Checkbox
                )

                if checkbox.value:
                    selected.append(sink_name)

            if len(selected) < 2:
                self.status.update("Select at least 2 outputs")
                return

            self.remove_combined_sinks()

            slaves = ",".join(selected)

            try:
                subprocess.check_output([
                    "pactl",
                    "load-module",
                    "module-combine-sink",
                    "sink_name=combined",
                    f"slaves={slaves}"
                ])

                subprocess.run([
                    "pactl",
                    "set-default-sink",
                    "combined"
                ])

                self.move_audio_streams()

                self.status.update(
                    f"Combined sink created with: {', '.join(selected)}"
                )

            except Exception as e:
                self.status.update(str(e))

        elif event.button.id == "remove":
            self.remove_combined_sinks()
            self.status.update("Combined sink removed")

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
                    "combined"
                ])

        except Exception:
            pass


if __name__ == "__main__":
    app = AudioCombineApp()
    app.run()
