import Foundation

// MARK: - Exercise Model

struct Exercise: Codable {
    let id: String
    let name: String
    let instruction: String
    let tier: Int
    let source: String
}

struct ExerciseData: Codable {
    let exercises: [Exercise]
    let quotes: [String]
}

// MARK: - ExerciseEngine

class ExerciseEngine {
    static let shared = ExerciseEngine()

    let exercises: [Exercise]
    let quotes: [String]

    private init() {
        guard let url = Bundle.main.url(forResource: "exercises", withExtension: "json") else {
            fatalError("exercises.json missing from app bundle — rebuild Arnie.app")
        }
        do {
            let data = try Data(contentsOf: url)
            let loaded = try JSONDecoder().decode(ExerciseData.self, from: data)
            guard !loaded.exercises.isEmpty, !loaded.quotes.isEmpty else {
                fatalError("exercises.json loaded but contains no exercises or quotes")
            }
            exercises = loaded.exercises
            quotes = loaded.quotes
        } catch {
            fatalError("Failed to load exercises.json: \(error.localizedDescription)")
        }
    }

    // MARK: Tier Logic

    func getCurrentTier(tierStartDate: String, tierDays: [Int]) -> Int {
        guard let start = dateFromISO(tierStartDate) else { return 1 }
        let daysElapsed = Calendar.current.dateComponents([.day], from: start, to: Date()).day ?? 0
        var tier = 1
        var cumulative = 0
        for duration in tierDays {
            cumulative += duration
            if daysElapsed >= cumulative {
                tier += 1
            } else {
                break
            }
        }
        return tier
    }

    func daysUntilNextTier(tierStartDate: String, tierDays: [Int]) -> Int? {
        guard let start = dateFromISO(tierStartDate) else { return nil }
        let daysElapsed = Calendar.current.dateComponents([.day], from: start, to: Date()).day ?? 0
        var cumulative = 0
        for duration in tierDays {
            cumulative += duration
            if daysElapsed < cumulative {
                return cumulative - daysElapsed
            }
        }
        return nil  // All tiers unlocked
    }

    func daysActive(tierStartDate: String) -> Int {
        guard let start = dateFromISO(tierStartDate) else { return 0 }
        return (Calendar.current.dateComponents([.day], from: start, to: Date()).day ?? 0)
    }

    func numTiers(tierDays: [Int]) -> Int {
        return tierDays.count + 1
    }

    // MARK: Exercise Selection

    func pickExercise(state: inout ArnieState, tierDays: [Int]) -> Exercise {
        let tier = getCurrentTier(tierStartDate: state.tierStartDate, tierDays: tierDays)
        let eligible = exercises.filter { $0.tier <= tier }
        var pool = eligible.filter { !state.todayShown.contains($0.id) }

        if pool.isEmpty {
            state.todayShown = []
            pool = eligible
        }

        return pool.randomElement()!
    }

    func eligibleCount(tierStartDate: String, tierDays: [Int]) -> Int {
        let tier = getCurrentTier(tierStartDate: tierStartDate, tierDays: tierDays)
        return exercises.filter { $0.tier <= tier }.count
    }

    func pickQuote() -> String {
        return quotes.randomElement() ?? "Let's go!"
    }

    // MARK: Helpers

    private func dateFromISO(_ string: String) -> Date? {
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        return fmt.date(from: string)
    }
}
