import Cocoa
import UserNotifications

// Arnie — Desk workout menu bar app
//
// If launched with args: fire one notification and exit (backward compat with Python CLI).
// If launched without args: start the menu bar app.

let args = CommandLine.arguments

if args.count > 1 {
    // Legacy one-shot mode: Arnie.app "Title" "Body" "Sound"
    let app = NSApplication.shared
    app.setActivationPolicy(.accessory)

    let title = args[1]
    let body = args.count > 2 ? args[2] : ""
    let sound = args.count > 3 ? args[3] : "Ping"

    NotificationManager.shared.sendOneShotAndExit(title: title, body: body, sound: sound)
} else {
    // Full menu bar app mode
    let app = NSApplication.shared
    app.setActivationPolicy(.accessory)

    let delegate = AppDelegate()
    app.delegate = delegate
    app.run()
}

// MARK: - AppDelegate

class AppDelegate: NSObject, NSApplicationDelegate {
    private let menuBar = MenuBarController()

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Request notification permission
        NotificationManager.shared.requestAuthorization()

        // Set up menu bar
        menuBar.setup()

        // Start the exercise timer
        TimerController.shared.onMenuUpdate = {
            // Menu rebuilds dynamically via NSMenuDelegate, nothing to do here
        }
        TimerController.shared.start()
    }
}
