package main

import (
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// ─── Styles ──────────────────────────────────────────────────────────────────

var (
	styleSelected   = lipgloss.NewStyle().Foreground(lipgloss.Color("2")).Bold(true)
	styleCursor     = lipgloss.NewStyle().Reverse(true)
	styleTitle      = lipgloss.NewStyle().Bold(true).Underline(true)
	styleFooter     = lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
	styleInfo       = lipgloss.NewStyle().Foreground(lipgloss.Color("6"))
	styleError      = lipgloss.NewStyle().Foreground(lipgloss.Color("1"))
	styleCheckOn    = lipgloss.NewStyle().Foreground(lipgloss.Color("2"))
	styleCheckOff   = lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
)

// ─── Model ───────────────────────────────────────────────────────────────────

type Sink struct {
	Name  string
	Label string
}

type Model struct {
	sinks    []Sink
	selected map[int]bool
	cursor   int
	message  string
	isError  bool
}

func initialModel() Model {
	m := Model{
		selected: make(map[int]bool),
		message:  "Ready",
	}

	if !checkSupport(&m) {
		return m
	}

	m.sinks = getSinks()
	m.loadExistingCombined()
	return m
}

// ─── Init / Update / View ────────────────────────────────────────────────────

func (m Model) Init() tea.Cmd {
	return nil
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit

		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}

		case "down", "j":
			if m.cursor < len(m.sinks)-1 {
				m.cursor++
			}

		case " ":
			if len(m.sinks) > 0 {
				m.selected[m.cursor] = !m.selected[m.cursor]
				if !m.selected[m.cursor] {
					delete(m.selected, m.cursor)
				}
			}

		case "enter":
			m.combineSelected()

		case "delete":
			m.removeCombinedSinks()
			m.selected = make(map[int]bool)
			m.message = "Combined sink removed"
			m.isError = false

		case "r":
			m.refreshSinks()
		}
	}

	return m, nil
}

func (m Model) View() string {
	var b strings.Builder

	b.WriteString(styleTitle.Render("Select audio outputs to combine:"))
	b.WriteString("\n\n")

	if len(m.sinks) == 0 {
		b.WriteString(styleError.Render("  No audio sinks found. Try pressing R to refresh."))
		b.WriteString("\n")
	}

	for idx, sink := range m.sinks {
		checkbox := styleCheckOff.Render("[ ]")
		label := sink.Label

		if m.selected[idx] {
			checkbox = styleCheckOn.Render("[x]")
			label = styleSelected.Render(label)
		}

		line := fmt.Sprintf("%s %s", checkbox, label)

		if idx == m.cursor {
			line = styleCursor.Render(fmt.Sprintf("%s %s", checkbox, sink.Label))
		}

		b.WriteString("  " + line + "\n")
	}

	b.WriteString("\n")
	b.WriteString(styleFooter.Render("SPACE=toggle  ENTER=combine  R=refresh  DEL=remove combined  Q=quit"))
	b.WriteString("\n\n")

	msgStyle := styleInfo
	if m.isError {
		msgStyle = styleError
	}
	b.WriteString(msgStyle.Render("[INFO] " + m.message))
	b.WriteString("\n")

	return b.String()
}

// ─── Audio Logic ─────────────────────────────────────────────────────────────

func checkSupport(m *Model) bool {
	if _, err := exec.LookPath("pactl"); err != nil {
		m.message = "Audio combine is not supported: missing 'pactl' (check: which pactl)"
		m.isError = true
		return false
	}

	if err := exec.Command("pactl", "info").Run(); err != nil {
		m.message = "PulseAudio/PipeWire unavailable (check: pactl info)"
		m.isError = true
		return false
	}

	return true
}

func getSinks() []Sink {
	out, err := exec.Command("pactl", "list", "short", "sinks").Output()
	if err != nil {
		return nil
	}

	var sinks []Sink
	wsRe := regexp.MustCompile(`\s+`)

	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		parts := wsRe.Split(strings.TrimSpace(line), -1)
		if len(parts) < 2 {
			continue
		}

		name := parts[1]
		if strings.HasPrefix(name, "Combined") {
			continue
		}

		label := resolveLabel(name)
		sinks = append(sinks, Sink{Name: name, Label: label})
	}

	return sinks
}

func resolveLabel(name string) string {
	switch {
	case strings.Contains(name, "Speaker"):
		return "Laptop Speaker"
	case strings.Contains(name, "HDMI1"):
		return "HDMI Output 1"
	case strings.Contains(name, "HDMI2"):
		return "HDMI Output 2"
	case strings.Contains(name, "HDMI3"):
		return "HDMI Output 3"
	case strings.HasPrefix(name, "bluez_output"):
		return resolveBluetoothLabel(name)
	default:
		return name
	}
}

func resolveBluetoothLabel(name string) string {
	out, err := exec.Command("pactl", "list", "sinks").Output()
	if err != nil {
		return name
	}

	descRe := regexp.MustCompile(`device\.description = "(.*?)"`)

	for _, block := range strings.Split(string(out), "Sink #") {
		if !strings.Contains(block, name) {
			continue
		}
		if m := descRe.FindStringSubmatch(block); m != nil {
			return "Bluetooth: " + m[1]
		}
	}

	return name
}

func removeCombinedSinksCmd() {
	out, err := exec.Command("pactl", "list", "short", "modules").Output()
	if err != nil {
		return
	}

	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		if !strings.Contains(line, "module-combine-sink") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) > 0 {
			exec.Command("pactl", "unload-module", parts[0]).Run() //nolint
		}
	}
}

func (m *Model) removeCombinedSinks() {
	removeCombinedSinksCmd()
}

func (m *Model) combineSelected() {
	var names, labels []string

	for idx, sink := range m.sinks {
		if m.selected[idx] {
			names = append(names, sink.Name)
			labels = append(labels, sink.Label)
		}
	}

	if len(names) == 0 {
		removeCombinedSinksCmd()
		m.message = "All combined sinks removed"
		m.isError = false
		return
	}

	if len(names) == 1 {
		m.message = "Select at least 2 outputs"
		m.isError = true
		return
	}

	removeCombinedSinksCmd()

	// Build a safe combined sink name
	sanitize := regexp.MustCompile(`[^a-zA-Z0-9_]`)
	var parts []string
	for _, l := range labels {
		parts = append(parts, sanitize.ReplaceAllString(l, ""))
	}
	combinedName := "Combined_" + strings.Join(parts, "_")
	slaves := strings.Join(names, ",")

	exec.Command("pactl", "load-module", "module-combine-sink",
		"sink_name="+combinedName,
		"slaves="+slaves,
	).Run() //nolint

	exec.Command("pactl", "set-default-sink", combinedName).Run() //nolint

	m.moveAudioStreams(combinedName)

	m.message = "Combined: " + strings.Join(labels, " + ")
	m.isError = false
}

func (m *Model) moveAudioStreams(combinedName string) {
	out, err := exec.Command("pactl", "list", "short", "sink-inputs").Output()
	if err != nil {
		return
	}

	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		if line == "" {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) > 0 {
			exec.Command("pactl", "move-sink-input", parts[0], combinedName).Run() //nolint
		}
	}
}

func (m *Model) loadExistingCombined() {
	out, err := exec.Command("pactl", "list", "short", "modules").Output()
	if err != nil {
		return
	}

	slavesRe := regexp.MustCompile(`slaves=([^ \t]+)`)

	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		if !strings.Contains(line, "module-combine-sink") {
			continue
		}
		match := slavesRe.FindStringSubmatch(line)
		if match == nil {
			continue
		}
		activeSlaves := strings.Split(match[1], ",")
		slaveSet := make(map[string]bool)
		for _, s := range activeSlaves {
			slaveSet[s] = true
		}
		for idx, sink := range m.sinks {
			if slaveSet[sink.Name] {
				m.selected[idx] = true
			}
		}
	}
}

func (m *Model) refreshSinks() {
	// Remember currently selected sink names
	oldNames := make(map[string]bool)
	for idx := range m.selected {
		if idx < len(m.sinks) {
			oldNames[m.sinks[idx].Name] = true
		}
	}

	m.sinks = getSinks()
	m.selected = make(map[int]bool)

	for idx, sink := range m.sinks {
		if oldNames[sink.Name] {
			m.selected[idx] = true
		}
	}

	if m.cursor >= len(m.sinks) && len(m.sinks) > 0 {
		m.cursor = len(m.sinks) - 1
	}

	m.message = "Device list refreshed"
	m.isError = false
}

// ─── Entry Point ─────────────────────────────────────────────────────────────

func main() {
	m := initialModel()

	if m.isError {
		fmt.Fprintln(os.Stderr, "")
		fmt.Fprintln(os.Stderr, "[ERROR]", m.message)
		fmt.Fprintln(os.Stderr, "")
		os.Exit(1)
	}

	p := tea.NewProgram(m)
	p.EnterAltScreen()
	if err := p.Start(); err != nil {
		fmt.Fprintln(os.Stderr, "Error:", err)
		os.Exit(1)
	}
}