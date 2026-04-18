import Foundation
import UserNotifications

class TimerController {
    static let shared = TimerController()

    private var timer: Timer?
    var onMenuUpdate: (() -> Void)?

    private var lastExercise: Exercise?
    var lastExerciseName: String? { lastExercise?.name }
    var lastExerciseInstruction: String? { lastExercise?.instruction }

    func start() {
        let config = DataManager.shared.loadConfig()
        scheduleTimer(intervalMinutes: config.frequencyMinutes)

        // Wire up notification actions
        NotificationManager.shared.onDone = { [weak self] exerciseID in
            var state = DataManager.shared.loadState()
            state.todayCompleted += 1
            DataManager.shared.saveState(state)
            if let ex = ExerciseEngine.shared.exercises.first(where: { $0.id == exerciseID }) {
                DataManager.shared.appendLog(exercise: ex, quote: "")
            }
            DispatchQueue.main.async { self?.onMenuUpdate?() }
        }
        NotificationManager.shared.onSkip = { [weak self] exerciseID in
            var state = DataManager.shared.loadState()
            state.todayShown.removeAll { $0 == exerciseID }
            DataManager.shared.saveState(state)
            self?.onMenuUpdate?()
        }
        NotificationManager.shared.onAnother = { [weak self] exerciseID in
            var state = DataManager.shared.loadState()
            state.todayShown.removeAll { $0 == exerciseID }
            DataManager.shared.saveState(state)
            self?.fireNow()
        }
    }

    func reschedule() {
        let config = DataManager.shared.loadConfig()
        scheduleTimer(intervalMinutes: config.frequencyMinutes)
    }

    func fireNow() {
        // Before firing, sweep away any un-acted-on prior notifications and
        // revert their rotation entries. Then fire fresh.
        supersedePriorNotifications { [weak self] in
            self?.actuallyFire()
        }
    }

    private func actuallyFire() {
        let config = DataManager.shared.loadConfig()
        let engine = ExerciseEngine.shared
        var state = DataManager.shared.loadState()

        // Reset daily counters on day rollover
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        let today = fmt.string(from: Date())
        if state.lastDate != today {
            state.todayShown = []
            state.todayCompleted = 0
            state.lastDate = today
        }

        let exercise = engine.pickExercise(state: &state, tierDays: config.tierDays)
        let quote = engine.pickQuote()

        let title = "Arnie: \(exercise.name)"
        let body = "\(exercise.instruction)\n\n\(quote)"

        NotificationManager.shared.sendNotification(
            title: title, body: body, sound: config.sound, exerciseID: exercise.id
        )

        state.todayShown.append(exercise.id)
        DataManager.shared.saveState(state)

        lastExercise = exercise
        onMenuUpdate?()
    }

    private func supersedePriorNotifications(then: @escaping () -> Void) {
        let center = UNUserNotificationCenter.current()
        center.getDeliveredNotifications { delivered in
            let ours = delivered.filter { $0.request.content.categoryIdentifier == "EXERCISE" }
            let notificationIDs = ours.map { $0.request.identifier }
            let exerciseIDs = ours.compactMap {
                $0.request.content.userInfo["exerciseID"] as? String
            }

            if !notificationIDs.isEmpty {
                center.removeDeliveredNotifications(withIdentifiers: notificationIDs)
            }

            DispatchQueue.main.async {
                if !exerciseIDs.isEmpty {
                    var state = DataManager.shared.loadState()
                    state.todayShown.removeAll { exerciseIDs.contains($0) }
                    DataManager.shared.saveState(state)
                }
                then()
            }
        }
    }

    // MARK: - Private

    private func scheduleTimer(intervalMinutes: Int) {
        timer?.invalidate()
        let interval = TimeInterval(intervalMinutes * 60)

        // Calculate seconds until the next aligned clock boundary
        let now = Date()
        let cal = Calendar.current
        let minute = cal.component(.minute, from: now)
        let second = cal.component(.second, from: now)

        let minutesSinceLastBoundary = minute % intervalMinutes
        let minutesUntilNext = intervalMinutes - minutesSinceLastBoundary
        let secondsUntilNext = TimeInterval(minutesUntilNext * 60 - second)

        // Fire once at the next boundary, then repeat on the interval
        timer = Timer.scheduledTimer(withTimeInterval: secondsUntilNext, repeats: false) { [weak self] _ in
            self?.timerFired()
            // Now start the repeating timer, aligned
            self?.timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
                self?.timerFired()
            }
        }
    }

    private func timerFired() {
        let config = DataManager.shared.loadConfig()
        let now = Date()
        let hour = Calendar.current.component(.hour, from: now)

        guard hour >= config.startHour && hour < config.endHour else {
            return  // Outside work hours
        }

        if config.weekdaysOnly {
            // Calendar weekday: 1 = Sunday, 7 = Saturday
            let weekday = Calendar.current.component(.weekday, from: now)
            guard weekday >= 2 && weekday <= 6 else { return }
        }

        fireNow()
    }
}
