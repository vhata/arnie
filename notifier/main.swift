import Cocoa
import UserNotifications

// Arnie notification sender — compiled into Arnie.app by `arnie.py install`.
// Usage: Arnie.app/Contents/MacOS/Arnie "Title" "Body text" "SoundName"

class NotificationDelegate: NSObject, UNUserNotificationCenterDelegate {
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound, .list])
    }
}

let args = CommandLine.arguments
let title = args.count > 1 ? args[1] : "Arnie"
let body = args.count > 2 ? args[2] : ""
let soundName = args.count > 3 ? args[3] : "Ping"

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

let delegate = NotificationDelegate()
let center = UNUserNotificationCenter.current()
center.delegate = delegate

let semaphore = DispatchSemaphore(value: 0)

center.requestAuthorization(options: [.alert, .sound]) { granted, error in
    guard granted else {
        fputs("Notifications not permitted. Allow Arnie in System Settings > Notifications.\n", stderr)
        exit(1)
    }

    let content = UNMutableNotificationContent()
    content.title = title
    content.body = body
    content.sound = UNNotificationSound(named: UNNotificationSoundName(soundName))

    let request = UNNotificationRequest(
        identifier: UUID().uuidString,
        content: content,
        trigger: nil
    )

    center.add(request) { error in
        if let error = error {
            fputs("Failed to send: \(error.localizedDescription)\n", stderr)
        }
        semaphore.signal()
    }
}

semaphore.wait()
Thread.sleep(forTimeInterval: 0.5)
exit(0)
