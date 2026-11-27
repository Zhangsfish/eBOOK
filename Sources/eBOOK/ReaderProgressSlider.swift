import SwiftUI
import UIKit

/// A small visible thumb with the native slider's full-height touch/VoiceOver control.
struct ReaderProgressSlider: UIViewRepresentable {
    @Binding var value: Double
    let color: UIColor
    let increasedContrast: Bool

    func makeUIView(context: Context) -> UISlider {
        let slider = UISlider()
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
        @objc func changed(_ slider: UISlider) { parent.value = Double(slider.value) }
    }
}
