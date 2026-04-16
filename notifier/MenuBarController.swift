import Cocoa
import ServiceManagement

class MenuBarController: NSObject, NSMenuDelegate {
    private var statusItem: NSStatusItem!
    private let menu = NSMenu()

    func setup() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        updateIcon()
        menu.delegate = self
        statusItem.menu = menu
    }

    func updateIcon() {
        guard let button = statusItem.button else { return }
        let config = DataManager.shared.loadConfig()
        if let img = NSImage(systemSymbolName: config.icon, accessibilityDescription: "Arnie") {
            img.isTemplate = true
            button.image = img
        } else {
            button.title = "💪"
        }
    }

    // MARK: - NSMenuDelegate

    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.removeAllItems()
        let config = DataManager.shared.loadConfig()
        let state = DataManager.shared.loadState()
        let engine = ExerciseEngine.shared

        // Last exercise shown
        if let name = TimerController.shared.lastExerciseName,
           let instr = TimerController.shared.lastExerciseInstruction {
            let nameItem = NSMenuItem(title: name, action: nil, keyEquivalent: "")
            nameItem.isEnabled = false
            nameItem.attributedTitle = NSAttributedString(
                string: name,
                attributes: [.font: NSFont.boldSystemFont(ofSize: 13)]
            )
            menu.addItem(nameItem)

            // Word-wrap the instruction into multiple menu items
            for line in wordWrap(instr, maxWidth: 45) {
                let lineItem = NSMenuItem(title: line, action: nil, keyEquivalent: "")
                lineItem.isEnabled = false
                menu.addItem(lineItem)
            }
            menu.addItem(.separator())
        }

        // Next Exercise button
        let nextItem = NSMenuItem(title: "Next Exercise", action: #selector(nextExercise), keyEquivalent: "n")
        nextItem.target = self
        menu.addItem(nextItem)

        menu.addItem(.separator())

        // Status
        let tier = engine.getCurrentTier(tierStartDate: state.tierStartDate, tierDays: config.tierDays)
        let numTiers = engine.numTiers(tierDays: config.tierDays)
        let day = engine.daysActive(tierStartDate: state.tierStartDate) + 1
        let eligible = engine.eligibleCount(tierStartDate: state.tierStartDate, tierDays: config.tierDays)
        let shown = state.todayShown.count

        let statusText = "Day \(day) · Tier \(tier)/\(numTiers) · \(shown)/\(eligible) exercises"
        let statusItem = NSMenuItem(title: statusText, action: nil, keyEquivalent: "")
        statusItem.isEnabled = false
        menu.addItem(statusItem)

        if let remaining = engine.daysUntilNextTier(tierStartDate: state.tierStartDate, tierDays: config.tierDays) {
            let tierItem = NSMenuItem(title: "Next tier in \(remaining) days", action: nil, keyEquivalent: "")
            tierItem.isEnabled = false
            menu.addItem(tierItem)
        } else {
            let tierItem = NSMenuItem(title: "All tiers unlocked!", action: nil, keyEquivalent: "")
            tierItem.isEnabled = false
            menu.addItem(tierItem)
        }

        menu.addItem(.separator())

        // Today's log submenu
        let logEntries = DataManager.shared.todayLogEntries()
        let logSubmenu = NSMenu()
        if logEntries.isEmpty {
            let emptyItem = NSMenuItem(title: "No exercises yet", action: nil, keyEquivalent: "")
            emptyItem.isEnabled = false
            logSubmenu.addItem(emptyItem)
        } else {
            for entry in logEntries {
                let item = NSMenuItem(title: entry, action: nil, keyEquivalent: "")
                item.isEnabled = false
                logSubmenu.addItem(item)
            }
        }
        let logItem = NSMenuItem(title: "Today's Log", action: nil, keyEquivalent: "")
        logItem.submenu = logSubmenu
        menu.addItem(logItem)

        menu.addItem(.separator())

        // Settings submenu
        let settingsSubmenu = NSMenu()
        addChoiceSubmenu(to: settingsSubmenu, title: "Start Hour",
                         choices: [7, 8, 9, 10, 11, 12], current: config.startHour,
                         format: { "\($0):00" }, action: #selector(setStartHour(_:)))
        addChoiceSubmenu(to: settingsSubmenu, title: "End Hour",
                         choices: [16, 17, 18, 19, 20, 21], current: config.endHour,
                         format: { "\($0):00" }, action: #selector(setEndHour(_:)))
        addChoiceSubmenu(to: settingsSubmenu, title: "Frequency",
                         choices: [15, 20, 30, 45, 60], current: config.frequencyMinutes,
                         format: { "\($0) min" }, action: #selector(setFrequency(_:)))
        addChoiceSubmenu(to: settingsSubmenu, title: "Sound",
                         choices: ["Ping", "Glass", "Basso", "Hero", "Morse", "Pop", "Purr", "Submarine", "Tink"],
                         current: config.sound,
                         action: #selector(setSound(_:)))
        addIconSubmenu(to: settingsSubmenu, current: config.icon)
        settingsSubmenu.addItem(.separator())

        let loginItem = NSMenuItem(title: "Start at Login", action: #selector(toggleLoginItem), keyEquivalent: "")
        loginItem.target = self
        if SMAppService.mainApp.status == .enabled {
            loginItem.state = .on
        }
        settingsSubmenu.addItem(loginItem)

        let settingsItem = NSMenuItem(title: "Settings", action: nil, keyEquivalent: "")
        settingsItem.submenu = settingsSubmenu
        menu.addItem(settingsItem)

        menu.addItem(.separator())

        // Reset
        let resetItem = NSMenuItem(title: "Reset Progression", action: #selector(resetProgression), keyEquivalent: "")
        resetItem.target = self
        menu.addItem(resetItem)

        menu.addItem(.separator())

        // Quit
        let quitItem = NSMenuItem(title: "Quit Arnie", action: #selector(quit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)
    }

    // MARK: - Choice Submenus (Int)

    private func addChoiceSubmenu(to parentMenu: NSMenu, title: String, choices: [Int],
                                  current: Int, format: (Int) -> String, action: Selector) {
        let sub = NSMenu()
        for choice in choices {
            let item = NSMenuItem(title: format(choice), action: action, keyEquivalent: "")
            item.target = self
            item.tag = choice
            if choice == current { item.state = .on }
            sub.addItem(item)
        }
        let item = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        item.submenu = sub
        parentMenu.addItem(item)
    }

    // Choice Submenus (String)
    private func addChoiceSubmenu(to parentMenu: NSMenu, title: String, choices: [String],
                                  current: String, action: Selector) {
        let sub = NSMenu()
        for choice in choices {
            let item = NSMenuItem(title: choice, action: action, keyEquivalent: "")
            item.target = self
            item.representedObject = choice
            if choice == current { item.state = .on }
            sub.addItem(item)
        }
        let item = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        item.submenu = sub
        parentMenu.addItem(item)
    }

    // Choice Submenus (Icon — with SF Symbol previews)
    private func addIconSubmenu(to parentMenu: NSMenu, current: String) {
        let icons: [(name: String, symbol: String)] = [
            ("Dumbbell", "dumbbell.fill"),
            ("Walking", "figure.walk"),
            ("Running", "figure.run"),
            ("Flexibility", "figure.flexibility"),
            ("Strengthtraining", "figure.strengthtraining.traditional"),
            ("Heart", "heart.fill"),
            ("Flame", "flame.fill"),
            ("Star", "star.fill"),
        ]
        let sub = NSMenu()
        for icon in icons {
            let item = NSMenuItem(title: icon.name, action: #selector(setIcon(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = icon.symbol
            if icon.symbol == current { item.state = .on }
            if let img = NSImage(systemSymbolName: icon.symbol, accessibilityDescription: icon.name) {
                img.isTemplate = true
                item.image = img
            }
            sub.addItem(item)
        }
        let item = NSMenuItem(title: "Icon", action: nil, keyEquivalent: "")
        item.submenu = sub
        parentMenu.addItem(item)
    }

    // MARK: - Actions

    @objc private func nextExercise() {
        TimerController.shared.fireNow()
    }

    @objc private func setStartHour(_ sender: NSMenuItem) {
        var config = DataManager.shared.loadConfig()
        config.startHour = sender.tag
        DataManager.shared.saveConfig(config)
        TimerController.shared.reschedule()
    }

    @objc private func setEndHour(_ sender: NSMenuItem) {
        var config = DataManager.shared.loadConfig()
        config.endHour = sender.tag
        DataManager.shared.saveConfig(config)
        TimerController.shared.reschedule()
    }

    @objc private func setFrequency(_ sender: NSMenuItem) {
        var config = DataManager.shared.loadConfig()
        config.frequencyMinutes = sender.tag
        DataManager.shared.saveConfig(config)
        TimerController.shared.reschedule()
    }

    @objc private func setSound(_ sender: NSMenuItem) {
        guard let sound = sender.representedObject as? String else { return }
        var config = DataManager.shared.loadConfig()
        config.sound = sound
        DataManager.shared.saveConfig(config)
        NSSound(named: NSSound.Name(sound))?.play()
    }

    @objc private func setIcon(_ sender: NSMenuItem) {
        guard let icon = sender.representedObject as? String else { return }
        var config = DataManager.shared.loadConfig()
        config.icon = icon
        DataManager.shared.saveConfig(config)
        updateIcon()
    }

    @objc private func toggleLoginItem() {
        let service = SMAppService.mainApp
        do {
            if service.status == .enabled {
                try service.unregister()
            } else {
                try service.register()
            }
        } catch {
            fputs("Login item error: \(error.localizedDescription)\n", stderr)
        }
    }

    @objc private func resetProgression() {
        let alert = NSAlert()
        alert.messageText = "Reset Progression?"
        alert.informativeText = "This will reset you back to Tier 1, Day 1. Your exercise log will be kept."
        alert.alertStyle = .warning
        alert.addButton(withTitle: "Reset")
        alert.addButton(withTitle: "Cancel")

        if alert.runModal() == .alertFirstButtonReturn {
            var state = DataManager.shared.loadState()
            let fmt = DateFormatter()
            fmt.dateFormat = "yyyy-MM-dd"
            state.tierStartDate = fmt.string(from: Date())
            state.todayShown = []
            state.lastDate = nil
            DataManager.shared.saveState(state)
        }
    }

    @objc private func quit() {
        NSApp.terminate(nil)
    }

    // MARK: - Helpers

    private func wordWrap(_ text: String, maxWidth: Int) -> [String] {
        var lines: [String] = []
        var current = ""
        for word in text.split(separator: " ") {
            if current.isEmpty {
                current = String(word)
            } else if current.count + 1 + word.count <= maxWidth {
                current += " " + word
            } else {
                lines.append(current)
                current = String(word)
            }
        }
        if !current.isEmpty { lines.append(current) }
        return lines
    }
}
