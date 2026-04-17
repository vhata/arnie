import Foundation

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
        NotificationManager.shared.onSkip = { [weak self] exerciseID in
            var state = DataManager.shared.loadState()
            state.todayShown.removeAll { $0 == exerciseID }
            DataManager.shared.saveState(state)
            self?.onMenuUpdate?()
        }
        NotificationManager.shared.onAnother = { [weak self] in
            self?.fireNow()
        }
    }

    func reschedule() {
        let config = DataManager.shared.loadConfig()
        scheduleTimer(intervalMinutes: config.frequencyMinutes)
    }

    func fireNow() {
        let config = DataManager.shared.loadConfig()
        let engine = ExerciseEngine.shared
        var state = DataManager.shared.loadState()

        // Reset today_shown if new day
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        let today = fmt.string(from: Date())
        if state.lastDate != today {
            state.todayShown = []
            state.lastDate = today
        }

        let exercise = engine.pickExercise(state: &state, tierDays: config.tierDays)
        let quote = engine.pickQuote()

        let title = "Arnie: \(exercise.name)"
        let body = "\(exercise.instruction)\n\n\(quote)"

        NotificationManager.shared.sendNotification(
            title: title, body: body, sound: config.sound, exerciseID: exercise.id
        )
        DataManager.shared.appendLog(exercise: exercise, quote: quote)

        state.todayShown.append(exercise.id)
        DataManager.shared.saveState(state)

        lastExercise = exercise
        onMenuUpdate?()
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
        let hour = Calendar.current.component(.hour, from: Date())

        guard hour >= config.startHour && hour < config.endHour else {
            return  // Outside work hours
        }

        fireNow()
    }
}
