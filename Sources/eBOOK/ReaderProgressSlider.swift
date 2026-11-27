import SwiftUI
import UIKit

/// A small visible thumb with the native slider's full-height touch/VoiceOver control.
struct ReaderProgressSlider: UIViewRepresentable {
    @Binding var value: Double
    let color: UIColor
    let increasedContrast: Bool

    func makeUIView(context: Context) -> UISlider {
        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        let slider: UISlider = arguments.contains("--uitesting") && arguments.contains("--test-seek-probe") ? ReaderSeekProbe() : UISlider()
        #else
        let slider = UISlider()
        #endif
        slider.minimumValue = 0; slider.maximumValue = 1
        slider.accessibilityLabel = "阅读进度"
        slider.accessibilityIdentifier = "reader.seek"
        slider.addTarget(context.coordinator, action: #selector(Coordinator.changed(_:)), for: .valueChanged)
        slider.setContentHuggingPriority(.defaultLow, for: .horizontal)
        return slider
    }

    func updateUIView(_ slider: UISlider, context: Context) {
        context.coordinator.parent = self
        if !slider.isTracking { slider.value = Float(value) }
        let ink = color.resolvedColor(with: slider.traitCollection)
        slider.minimumTrackTintColor = ink.withAlphaComponent(increasedContrast ? 1 : 0.55)
        slider.maximumTrackTintColor = ink.withAlphaComponent(increasedContrast ? 0.45 : 0.16)
        let thumbColor = ink.withAlphaComponent(increasedContrast ? 1 : 0.75)
        // UIKit tracks using the thumb image's bounds. Keep a44pt transparent
        // thumb around the12pt visible dot, including at either end of the track.
        // Replacing the thumb during every drag update can also disturb tracking.
        if context.coordinator.thumbColor?.isEqual(thumbColor) != true {
            let thumb = UIGraphicsImageRenderer(size: CGSize(width: 44, height: 44)).image { context in
                thumbColor.setFill()
                context.cgContext.fillEllipse(in: CGRect(x: 16, y: 16, width: 12, height: 12))
            }
            slider.setThumbImage(thumb, for: .normal)
            slider.setThumbImage(thumb, for: .highlighted)
            context.coordinator.thumbColor = thumbColor
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject {
        var parent: ReaderProgressSlider
        var thumbColor: UIColor?
        init(_ parent: ReaderProgressSlider) { self.parent = parent }
        @objc func changed(_ slider: UISlider) {
            #if DEBUG
            (slider as? ReaderSeekProbe)?.recordAction()
            #endif
            parent.value = Double(slider.value)
        }
    }
}

#if DEBUG
/// Live geometry/event counters for the isolated original-fixture UI tests only.
/// Normal Debug launches and every Release build use the stock UISlider above.
private final class ReaderSeekProbe: UISlider {
    private var begins = 0, moves = 0, actions = 0
    private var accepted = false
    private var lastAction: Float = 0
    private var firstPoint = CGPoint.zero

    override var accessibilityValue: String? {
        get {
            let thumb = thumbRect(forBounds: bounds, trackRect: trackRect(forBounds: bounds), value: value)
            let point = convert(CGPoint(x: thumb.midX, y: thumb.midY), to: nil)
            return "value=\(value);screenX=\(point.x);screenY=\(point.y);width=\(bounds.width);height=\(bounds.height);begins=\(begins);accepted=\(accepted);moves=\(moves);actions=\(actions);lastAction=\(lastAction);firstX=\(firstPoint.x);firstY=\(firstPoint.y)"
        }
        set { super.accessibilityValue = newValue }
    }
    override func beginTracking(_ touch: UITouch, with event: UIEvent?) -> Bool {
        begins += 1; firstPoint = touch.location(in: self)
        accepted = super.beginTracking(touch, with: event)
        return accepted
    }
    override func continueTracking(_ touch: UITouch, with event: UIEvent?) -> Bool {
        moves += 1
        return super.continueTracking(touch, with: event)
    }
    func recordAction() { actions += 1; lastAction = value }
}
#endif
