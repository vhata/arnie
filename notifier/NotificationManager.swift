import Cocoa
import UserNotifications

// MARK: - NotificationManager

class NotificationManager: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationManager()

    private let center = UNUserNotificationCenter.current()
    private let categoryID = "EXERCISE"

    var onSkip: ((String) -> Void)?   // Called with exercise ID
    var onAnother: (() -> Void)?      // Called to trigger next exercise

    override init() {
        super.init()
        center.delegate = self
        registerCategories()
    }

    func requestAuthorization() {
        center.requestAuthorization(options: [.alert, .sound]) { granted, error in
            if !granted {
                fputs("Notification permission denied. Enable in System Settings > Notifications > Arnie.\n", stderr)
            }
        }
    }

    private func registerCategories() {
        let done = UNNotificationAction(identifier: "DONE", title: "Done", options: [])
        let skip = UNNotificationAction(identifier: "SKIP", title: "Skip", options: [])
        let another = UNNotificationAction(identifier: "ANOTHER", title: "Another", options: [])

        let category = UNNotificationCategory(
            identifier: categoryID,
            actions: [done, skip, another],
            intentIdentifiers: []
        )
        center.setNotificationCategories([category])
    }

    func sendNotification(title: String, body: String, sound: String, exerciseID: String) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = UNNotificationSound(named: UNNotificationSoundName(sound))
        content.categoryIdentifier = categoryID
        content.userInfo = ["exerciseID": exerciseID]

        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )

        center.add(request) { error in
            if let error = error {
                fputs("Notification error: \(error.localizedDescription)\n", stderr)
            }
        }
    }

    // One-shot mode for backward compat with Python CLI
    func sendOneShotAndExit(title: String, body: String, sound: String) {
        let semaphore = DispatchSemaphore(value: 0)

        center.requestAuthorization(options: [.alert, .sound]) { granted, _ in
            guard granted else {
                fputs("Notifications not permitted.\n", stderr)
                exit(1)
            }

            let content = UNMutableNotificationContent()
            content.title = title
            content.body = body
            content.sound = UNNotificationSound(named: UNNotificationSoundName(sound))

            let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
            self.center.add(request) { _ in
                semaphore.signal()
            }
        }

        semaphore.wait()
        Thread.sleep(forTimeInterval: 0.5)
        exit(0)
    }

    // MARK: - UNUserNotificationCenterDelegate

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound, .list])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let exerciseID = response.notification.request.content.userInfo["exerciseID"] as? String ?? ""

        switch response.actionIdentifier {
        case "SKIP":
            onSkip?(exerciseID)
        case "ANOTHER":
            onAnother?()
        case "DONE", UNNotificationDefaultActionIdentifier:
            break  // Already tracked in today_shown
        default:
            break
        }

        completionHandler()
    }
}
