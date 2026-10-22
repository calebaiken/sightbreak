// Read-only OS capture and OCR. This executable never creates/posts input events.
import AppKit
import CoreGraphics
import ScreenCaptureKit
import Vision
import ImageIO
import UniformTypeIdentifiers
import Darwin

struct CaptureFailure: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

func rectValues(_ rect: CGRect) -> [Double] {
    [Double(rect.minX), Double(rect.minY), Double(rect.width), Double(rect.height)]
}

func closeRect(_ lhs: CGRect, _ rhs: CGRect) -> Bool {
    zip(rectValues(lhs), rectValues(rhs)).allSatisfy { abs($0.0 - $0.1) <= 0.5 }
}

func ownedWindow(_ pid: pid_t, _ windowID: CGWindowID) throws -> CGRect {
    guard let entries = CGWindowListCopyWindowInfo([.optionIncludingWindow, .excludeDesktopElements], windowID) as? [[String: Any]],
          let entry = entries.first(where: {
              ($0[kCGWindowNumber as String] as? NSNumber)?.uint32Value == windowID &&
              ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid &&
              ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 &&
              ($0[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue == true
          }),
          let dictionary = entry[kCGWindowBounds as String] as? [String: Any],
          let frame = CGRect(dictionaryRepresentation: dictionary as CFDictionary),
          !frame.isEmpty, !frame.isInfinite, !frame.isNull else {
        throw CaptureFailure("CGWindowListCopyWindowInfo: exact owned visible layer-zero window unavailable")
    }
    return frame
}

@main
struct WindowCapture {
    @MainActor
    static func main() async {
        var report: [String: Any] = [
            "scope": "OS window screenshot from ScreenCaptureKit; read-only helper",
            "passed": false, "input_events_posted": 0, "permission_requests_made": 0
        ]
        var reportURL: URL?
        var exitCode: Int32 = 1
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            guard args.count == 8 else { throw CaptureFailure("Expected --pid PID --window ID --png PATH --report PATH") }
            var options: [String: String] = [:]
            for offset in stride(from: 0, to: args.count, by: 2) {
                guard ["--pid", "--window", "--png", "--report"].contains(args[offset]), options[args[offset]] == nil else {
                    throw CaptureFailure("Unknown or repeated capture argument")
                }
                options[args[offset]] = args[offset + 1]
            }
            guard let pid = Int32(options["--pid"] ?? ""), pid > 0,
                  let windowID = UInt32(options["--window"] ?? ""), windowID > 0,
                  let png = options["--png"], let destination = options["--report"] else {
                throw CaptureFailure("Invalid owned-window capture arguments")
            }
            let pngURL = URL(fileURLWithPath: png)
            let candidateReport = URL(fileURLWithPath: destination)
            guard !FileManager.default.fileExists(atPath: pngURL.path),
                  !FileManager.default.fileExists(atPath: candidateReport.path) else {
                throw CaptureFailure("Preserve existing capture evidence")
            }
            reportURL = candidateReport
            let permissions = ["CGPreflightScreenCaptureAccess": CGPreflightScreenCaptureAccess(),
                               "CGPreflightPostEventAccess": CGPreflightPostEventAccess()]
            report["permissions"] = permissions
            guard permissions["CGPreflightScreenCaptureAccess"] == true else {
                throw CaptureFailure("Capture-helper non-requesting permission preflight denied")
            }
            let frame = try ownedWindow(pid, windowID)
            let available = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
            guard let window = available.windows.first(where: {
                $0.windowID == windowID && $0.owningApplication?.processID == pid && $0.windowLayer == 0
            }) else { throw CaptureFailure("SCShareableContent: exact owned window unavailable") }
            report["owner_pid"] = pid
            report["window_id"] = windowID
            report["bounds_points_including_chrome"] = rectValues(frame)
            report["scwindow_frame_points"] = rectValues(window.frame)
            let filter = SCContentFilter(desktopIndependentWindow: window)
            let rect = filter.contentRect
            let scale = Double(filter.pointPixelScale)
            report["filter_content_rect_points"] = rectValues(rect)
            report["point_pixel_scale"] = scale
            guard closeRect(frame, window.frame),
                  abs(rect.width - frame.width) <= 0.5, abs(rect.height - frame.height) <= 0.5,
                  scale.isFinite, scale > 0, scale <= 4 else {
                throw CaptureFailure("Unknown chrome/DPI geometry; no coordinate mapping authorized")
            }
            let configuration = SCStreamConfiguration()
            configuration.capturesAudio = false
            configuration.showsCursor = false
            configuration.ignoreShadowsSingleWindow = true
            configuration.width = Int(ceil(Double(rect.width) * scale))
            configuration.height = Int(ceil(Double(rect.height) * scale))
            let image = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: configuration)
            report["image_dimensions"] = [image.width, image.height]
            guard image.width == configuration.width, image.height == configuration.height,
                  closeRect(frame, try ownedWindow(pid, windowID)) else {
                throw CaptureFailure("Captured pixel dimensions or owned-window bounds changed")
            }
            guard let output = CGImageDestinationCreateWithURL(pngURL as CFURL, UTType.png.identifier as CFString, 1, nil) else {
                throw CaptureFailure("CGImageDestinationCreateWithURL failed")
            }
            CGImageDestinationAddImage(output, image, nil)
            guard CGImageDestinationFinalize(output) else { throw CaptureFailure("CGImageDestinationFinalize failed") }
            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            request.recognitionLanguages = ["en-US"]
            request.usesLanguageCorrection = false
            try VNImageRequestHandler(cgImage: image, options: [:]).perform([request])
            report["text"] = (request.results ?? []).compactMap { observation -> [String: Any]? in
                guard let candidate = observation.topCandidates(1).first else { return nil }
                return ["text": candidate.string, "confidence": candidate.confidence,
                        "box_normalized_bottom_left": rectValues(observation.boundingBox)]
            }
            report["passed"] = true
            exitCode = 0
        } catch {
            let native = error as NSError
            report["failure"] = ["domain": native.domain, "code": native.code,
                                 "message": String(describing: error), "localized_description": native.localizedDescription]
        }
        do {
            let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            if let url = reportURL { try data.write(to: url, options: .atomic) }
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data("\n".utf8))
        } catch {
            FileHandle.standardError.write(Data(("Capture report write failed: \(error)\n").utf8))
            exitCode = 1
        }
        Darwin.exit(exitCode)
    }
}
