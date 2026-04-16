import Foundation

// MARK: - Data Models

struct ArnieConfig: Codable {
    var startHour: Int
    var endHour: Int
    var frequencyMinutes: Int
    var tierDays: [Int]
    var sound: String
    var startAtLogin: Bool
    var icon: String

    enum CodingKeys: String, CodingKey {
        case startHour = "start_hour"
        case endHour = "end_hour"
        case frequencyMinutes = "frequency_minutes"
        case tierDays = "tier_days"
        case sound
        case startAtLogin = "start_at_login"
        case icon
    }

    static let defaults = ArnieConfig(
        startHour: 10,
        endHour: 19,
        frequencyMinutes: 30,
        tierDays: [14, 14],
        sound: "Ping",
        startAtLogin: false,
        icon: "dumbbell.fill"
    )

    init(startHour: Int = 10, endHour: Int = 19, frequencyMinutes: Int = 30,
         tierDays: [Int] = [14, 14], sound: String = "Ping", startAtLogin: Bool = false,
         icon: String = "dumbbell.fill") {
        self.startHour = startHour
        self.endHour = endHour
        self.frequencyMinutes = frequencyMinutes
        self.tierDays = tierDays
        self.sound = sound
        self.startAtLogin = startAtLogin
        self.icon = icon
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        let d = ArnieConfig.defaults
        startHour = (try? c.decode(Int.self, forKey: .startHour)) ?? d.startHour
        endHour = (try? c.decode(Int.self, forKey: .endHour)) ?? d.endHour
        frequencyMinutes = (try? c.decode(Int.self, forKey: .frequencyMinutes)) ?? d.frequencyMinutes
        tierDays = (try? c.decode([Int].self, forKey: .tierDays)) ?? d.tierDays
        sound = (try? c.decode(String.self, forKey: .sound)) ?? d.sound
        startAtLogin = (try? c.decode(Bool.self, forKey: .startAtLogin)) ?? d.startAtLogin
        icon = (try? c.decode(String.self, forKey: .icon)) ?? d.icon
    }
}

struct ArnieState: Codable {
    var tierStartDate: String
    var lastDate: String?
    var todayShown: [String]

    enum CodingKeys: String, CodingKey {
        case tierStartDate = "tier_start_date"
        case lastDate = "last_date"
        case todayShown = "today_shown"
    }

    static func makeDefault() -> ArnieState {
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        return ArnieState(
            tierStartDate: fmt.string(from: Date()),
            lastDate: nil,
            todayShown: []
        )
    }
}

// MARK: - DataManager

class DataManager {
    static let shared = DataManager()

    let appSupportDir: URL

    private init() {
        let fm = FileManager.default
        let appSupport = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        appSupportDir = appSupport.appendingPathComponent("Arnie")
        try? fm.createDirectory(at: appSupportDir, withIntermediateDirectories: true)
        try? fm.createDirectory(at: logsDir, withIntermediateDirectories: true)
    }

    var configFile: URL { appSupportDir.appendingPathComponent("config.json") }
    var stateFile: URL { appSupportDir.appendingPathComponent("state.json") }
    var logsDir: URL { appSupportDir.appendingPathComponent("logs") }

    // MARK: Config

    func loadConfig() -> ArnieConfig {
        guard let data = try? Data(contentsOf: configFile),
              let config = try? JSONDecoder().decode(ArnieConfig.self, from: data) else {
            return .defaults
        }
        return config
    }

    func saveConfig(_ config: ArnieConfig) {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        guard let data = try? encoder.encode(config) else { return }
        atomicWrite(data: data, to: configFile)
    }

    // MARK: State

    func loadState() -> ArnieState {
        guard let data = try? Data(contentsOf: stateFile),
              let state = try? JSONDecoder().decode(ArnieState.self, from: data) else {
            return .makeDefault()
        }
        return state
    }

    func saveState(_ state: ArnieState) {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        guard let data = try? encoder.encode(state) else { return }
        atomicWrite(data: data, to: stateFile)
    }

    // MARK: Logging

    func appendLog(exercise: Exercise, quote: String) {
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        let logFile = logsDir.appendingPathComponent("\(fmt.string(from: Date())).log")

        let timeFmt = DateFormatter()
        timeFmt.dateFormat = "HH:mm"
        let line = "\(timeFmt.string(from: Date()))  \(exercise.name) — \(exercise.instruction)\n"

        if let handle = try? FileHandle(forWritingTo: logFile) {
            handle.seekToEndOfFile()
            handle.write(line.data(using: .utf8)!)
            handle.closeFile()
        } else {
            try? line.write(to: logFile, atomically: true, encoding: .utf8)
        }
    }

    func todayLogEntries() -> [String] {
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        let logFile = logsDir.appendingPathComponent("\(fmt.string(from: Date())).log")
        guard let content = try? String(contentsOf: logFile, encoding: .utf8) else { return [] }
        return content.components(separatedBy: "\n").filter { !$0.isEmpty }
    }

    // MARK: Helpers

    private func atomicWrite(data: Data, to url: URL) {
        let tmp = url.appendingPathExtension("tmp")
        do {
            try data.write(to: tmp, options: .atomic)
            _ = try FileManager.default.replaceItemAt(url, withItemAt: tmp)
        } catch {
            // Fallback: direct write
            try? data.write(to: url)
        }
    }
}
