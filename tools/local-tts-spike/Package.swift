// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "LocalTTSSpike",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "LocalTTSSpike", targets: ["LocalTTSSpike"])],
    dependencies: [
        .package(url: "https://github.com/k2-fsa/sherpa-onnx",
                 revision: "38016c6e0622e90bf417c35e8b47e0eb805af417")
    ],
    targets: [
        .target(name: "LocalTTSSpike", dependencies: [
            .product(name: "sherpa-onnx", package: "sherpa-onnx")
        ]),
        .testTarget(name: "LocalTTSSpikeTests", dependencies: ["LocalTTSSpike"],
                    resources: [.copy("Resources")])
    ]
)
